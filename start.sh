#!/bin/bash

# Cloud Run startup script for Django/Wagtail application

set -e

echo "Starting Django application setup..."


# ===== Enhanced Environment Variable Debugging =====
echo "Environment check:"
echo "CLOUD_RUN: ${CLOUD_RUN:-'not set'}"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-'not set'}"
echo "PORT: ${PORT:-'not set'}"
echo "GCP_PROJECT: ${GCP_PROJECT:-'not set'}"
echo "DB_NAME: ${DB_NAME:-'not set'}"
echo "DB_USER: ${DB_USER:-'not set'}"
echo "DB_HOST: ${DB_HOST:-'not set'}"
echo "DB_PORT: ${DB_PORT:-'not set'}"
echo "DB_SSLKEY: ${DB_SSLKEY:-'not set'}"
echo "DB_SSLCERT: ${DB_SSLCERT:-'not set'}"
echo "DB_SSLROOTCERT: ${DB_SSLROOTCERT:-'not set'}"
echo "GS_BUCKET_NAME: ${GS_BUCKET_NAME:-'not set'}"
echo "WAGTAILADMIN_BASE_URL: ${WAGTAILADMIN_BASE_URL:-'not set'}"
echo "SUPERUSER_NAME: ${SUPERUSER_NAME:-'not set'}"

# Check if secret is accessible
if [ -n "$SECRET_KEY" ]; then
    echo "Secrets loaded successfully"
else
    echo "WARNING: SECRET_KEY not found - checking secrets..."
    echo "Available env vars:"
    env | grep -E "DB_|SECRET|GCP" | sed 's/=.*/=***/' || echo "No secrets found"
fi

# ===== Certificate Verification Section (NEW) =====
if [ -n "$DB_SSLKEY" ]; then
    echo "Verifying SSL certificate files..."
    
    if [ ! -f "$DB_SSLKEY" ] || [ ! -r "$DB_SSLKEY" ]; then
        echo "ERROR: SSL client key not found or not readable at: $DB_SSLKEY"
        exit 1
    fi
    
    if [ ! -f "$DB_SSLCERT" ] || [ ! -r "$DB_SSLCERT" ]; then
        echo "ERROR: SSL client certificate not found or not readable at: $DB_SSLCERT"
        exit 1
    fi
    
    if [ ! -f "$DB_SSLROOTCERT" ] || [ ! -r "$DB_SSLROOTCERT" ]; then
        echo "ERROR: SSL CA certificate not found or not readable at: $DB_SSLROOTCERT"
        exit 1
    fi
    
    echo "✓ All SSL certificates verified and accessible"
else
    echo "No SSL configuration detected - using standard connection"
fi

# ===== Enhanced Database Creation with SSL Support =====
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

# SSL certificate paths
db_sslkey = os.environ.get('DB_SSLKEY')
db_sslcert = os.environ.get('DB_SSLCERT')
db_sslrootcert = os.environ.get('DB_SSLROOTCERT')

if db_name and db_user and db_password and db_host:
    try:
        # Prepare connection parameters
        conn_params = {
            'dbname': 'postgres',  # Connect to default postgres database
            'user': db_user,
            'password': db_password,
            'host': db_host,
            'port': db_port
        }
        
        # Add SSL parameters if certificates are available
        if db_sslkey and db_sslcert and db_sslrootcert:
            conn_params.update({
                'sslmode': 'require',
                'sslkey': db_sslkey,
                'sslcert': db_sslcert,
                'sslrootcert': db_sslrootcert
            })
            print("Using SSL connection with client certificates")
        else:
            print("Using standard connection (no SSL certificates)")
        
        # Connect to PostgreSQL server
        conn = psycopg2.connect(**conn_params)
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

# ===== Database Connectivity Check =====
echo "Checking database connection..."
python manage.py check --database default || {
    echo "ERROR: Database check failed!"
    exit 1
}

# ===== Database Migrations =====
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "ERROR: Migrations failed!"
    exit 1
}

# ===== Static Files Collection =====
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --no-post-process || echo "Static files collection had warnings, but continuing..."

# ===== Superuser Creation =====
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

# ===== Gunicorn Server Startup =====
echo "Starting Gunicorn server..."
# For a single vCPU (1000m) a good default is 3 workers (2*1+1) and 2 threads.
WORKERS=${GUNICORN_WORKERS:-3}
THREADS=${GUNICORN_THREADS:-2}

echo "Starting Gunicorn with $WORKERS workers, $THREADS threads per worker (assumes 1 vCPU)"

exec gunicorn prabuddh_me.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers "$WORKERS" \
    --worker-class gthread \
    --threads "$THREADS" \
    --worker-connections 1000 \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
