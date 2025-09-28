#!/bin/bash

# Cloud Run startup script for Django/Wagtail application

set -e

echo "Starting Django application setup..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py create_superuser

echo "Starting Gunicorn server..."
exec gunicorn prabuddh_me.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class gthread \
    --worker-connections 1000 \
    --timeout 120 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info