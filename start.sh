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

# Check if secret is accessible
if [ -n "$PRABUDDH_ME_SECRETS" ]; then
    echo "Secret Manager secrets loaded successfully"
else
    echo "WARNING: PRABUDDH_ME_SECRETS not found"
fi

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
    --timeout 300 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info