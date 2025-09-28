#!/bin/bash

# Local development setup script

set -e

echo "Setting up local development environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your actual values"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser if needed
echo "Creating superuser if needed..."
python manage.py create_superuser

# Collect static files (for local development)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Setup complete! You can now run:"
echo "  python manage.py runserver"