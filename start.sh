#!/bin/bash

# Django/Wagtail startup script for Hetzner VM

set -e

echo "Starting Django application setup..."

# ===== Environment Variable Check =====
echo "Environment check:"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-'not set'}"
echo "DB_NAME: ${DB_NAME:-'not set'}"
echo "DB_USER: ${DB_USER:-'not set'}"
echo "DB_HOST: ${DB_HOST:-'not set'}"
echo "DB_PORT: ${DB_PORT:-'not set'}"
echo "WAGTAILADMIN_BASE_URL: ${WAGTAILADMIN_BASE_URL:-'not set'}"

if [ -n "$SECRET_KEY" ]; then
    echo "✓ SECRET_KEY loaded"
else
    echo "ERROR: SECRET_KEY not found!"
    exit 1
fi

# ===== Database Creation =====
echo "Ensuring database exists..."
python <<EOF || echo "Database creation check failed, attempting to continue..."
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST', 'db')
db_port = os.environ.get('DB_PORT', '5432')

if db_name and db_user and db_password and db_host:
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            print(f"✓ Database '{db_name}' created successfully")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"WARNING: Could not create database: {e}")
else:
    print("Database variables not set, skipping database creation...")
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
python manage.py collectstatic --noinput || echo "Static files collection had warnings, but continuing..."

# ===== Superuser Creation =====
if [ -n "$SUPERUSER_NAME" ] && [ -n "$SUPERUSER_EMAIL" ] && [ -n "$SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser if it doesn't exist..."
    python manage.py shell <<EOF || echo "WARNING: Superuser creation failed, but continuing..."
from django.contrib.auth import get_user_model

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
EOF
else
    echo "Skipping superuser creation (environment variables not set)"
fi

# ===== Gunicorn Server Startup =====
echo "Starting Gunicorn server..."
WORKERS=${GUNICORN_WORKERS:-3}
THREADS=${GUNICORN_THREADS:-2}

echo "Starting Gunicorn with $WORKERS workers, $THREADS threads per worker"

exec gunicorn prabuddh_me.wsgi:application \
    --bind 0.0.0.0:8000 \
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
