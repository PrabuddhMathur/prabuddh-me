#!/bin/bash

# Cloud Run startup script for Django/Wagtail application

set -e

echo "Starting Django application setup..."

# Debug environment variables
echo "Environment check:"
echo "CLOUD_RUN: ${CLOUD_RUN:-'not set'}"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-'not set'}"
echo "PORT: ${PORT:-'not set'}"
echo "GCP_PROJECT: ${GCP_PROJECT:-'not set'}"

if [ -d "/var/secrets/db-ca-cert" ]; then
    echo "Setting up SSL certificates..."
    mkdir -p /tmp/db-certs
    
    cp /var/secrets/db-client-key/db-client-key /tmp/db-certs/client-key.pem
    cp /var/secrets/db-client-cert/db-client-cert /tmp/db-certs/client-cert.pem
    cp /var/secrets/db-ca-cert/db-ca-cert /tmp/db-certs/ca-cert.pem
    
    chmod 600 /tmp/db-certs/client-key.pem
    chmod 644 /tmp/db-certs/client-cert.pem
    chmod 644 /tmp/db-certs/ca-cert.pem
    
    # Export env vars for Django to use
    export DB_SSLCERT=/tmp/db-certs/client-cert.pem
    export DB_SSLKEY=/tmp/db-certs/client-key.pem
    export DB_SSLROOTCERT=/tmp/db-certs/ca-cert.pem
    
    echo "✓ SSL certificates configured"
else
    echo "No SSL certificates mounted, skipping SSL setup"
fi
# Check if secret is accessible
if [ -n "$SECRET_KEY" ]; then
    echo "Secrets loaded successfully"
else
    echo "WARNING: SECRET_KEY not found - checking secrets..."
    echo "Available env vars:"
    env | grep -E "DB_|SECRET|GCP" | sed 's/=.*/=***/' || echo "No secrets found"
fi

# Create database if it doesn't exist (PostgreSQL only)
echo "Ensuring database exists..."
python <<EOF || echo "Database creation check failed, attempting to continue..."
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Get database connection details from environment
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_port = os.environ.get('DB_PORT', '5432')

if db_name and db_user and db_password and db_host:
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            dbname='postgres',  # Connect to default postgres database
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            print(f"✓ Database '{db_name}' created successfully")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"WARNING: Could not create database: {e}")
        print("Assuming database already exists or using SQLite...")
else:
    print("Using SQLite or database variables not set, skipping database creation...")
EOF

# Check database connectivity
echo "Checking database connection..."
python manage.py check --database default || {
    echo "ERROR: Database check failed!"
    exit 1
}

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "ERROR: Migrations failed!"
    exit 1
}

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --no-post-process || echo "Static files collection had warnings, but continuing..."

# Create superuser if environment variables are set
if [ -n "$SUPERUSER_NAME" ] && [ -n "$SUPERUSER_EMAIL" ] && [ -n "$SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser if it doesn't exist..."
    python manage.py shell <<EOF || echo "WARNING: Superuser creation failed, but continuing..."
from django.contrib.auth import get_user_model
import sys

try:
    User = get_user_model()
    username = "$SUPERUSER_NAME"
    email = "$SUPERUSER_EMAIL"
    password = "$SUPERUSER_PASSWORD"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✓ Superuser '{username}' created successfully")
    else:
        print(f"✓ Superuser '{username}' already exists")
except Exception as e:
    print(f"ERROR: Failed to create superuser: {e}")
    sys.exit(1)
EOF
else
    echo "Skipping superuser creation (environment variables not set)"
fi

echo "Starting Gunicorn server..."
exec gunicorn prabuddh_me.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class gthread \
    --worker-connections 1000 \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info