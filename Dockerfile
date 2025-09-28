# Base image: Python 3.12 slim
FROM python:3.12-slim-bookworm

# Create non-root user
RUN useradd wagtail

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=prabuddh_me.settings

# Install system dependencies
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    git \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=wagtail:wagtail . .

# Collect static files (Cloud Run ephemeral filesystem, only needed for container)
RUN python manage.py collectstatic --noinput --clear

# Ensure non-root user owns files
RUN chown -R wagtail:wagtail /app

# Switch to non-root user
USER wagtail

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Runtime command: Gunicorn app server
CMD ["gunicorn", "prabuddh_me.wsgi:application", "--bind", "0.0.0.0:8080"]
