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
if [ -n "$SECRET_KEY" ]; then
    echo "Secrets loaded successfully"
else
    echo "WARNING: SECRET_KEY not found - checking secrets..."
    echo "Available env vars:"
    env | grep -E "DB_|SECRET|GCP" | sed 's/=.*/=***/' || echo "No secrets found"
fi

# Skip migrations on startup - run them separately via Cloud Run jobs
# This allows the container to start and be healthy even if migrations fail
echo "Skipping migrations on startup (run separately via jobs/manual deployment)..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --no-post-process || echo "Static files collection had warnings, but continuing..."

# Skip superuser creation on startup too
echo "Skipping superuser creation on startup..."

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