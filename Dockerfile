# Multi-stage build: First stage for Google Cloud SDK
FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:495.0.0-slim AS gcloud

# Main stage: Python 3.12 slim
FROM python:3.12-slim-bookworm

# Create non-root user early
RUN useradd --create-home --shell /bin/bash wagtail

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production \
    PYTHONDONTWRITEBYTECODE=1

# \=============================================================================
# GOOGLE CLOUD AUTHENTICATION CONFIGURATION
# \=============================================================================
# This Dockerfile supports multiple Google Cloud authentication methods:
#
# 1. WORKLOAD IDENTITY (Recommended for GKE/Cloud Run):
#    - No additional setup needed in container
#    - Authentication handled by GKE/Cloud Run metadata service
#    - Most secure option for production deployments
#    - Set GOOGLE_APPLICATION_CREDENTIALS="" or leave unset
#
# 2. SERVICE ACCOUNT KEY FILES (For development/testing):
#    - Mount service account JSON key as volume to /etc/gcp/service-account/
#    - Set GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp/service-account/key.json
#    - Example: docker run -v /path/to/key.json:/etc/gcp/service-account/key.json
#
# 3. APPLICATION DEFAULT CREDENTIALS:
#    - Uses gcloud auth application-default login credentials
#    - Mount ~/.config/gcloud to /home/wagtail/.config/gcloud
#    - Suitable for local development
#
# 4. DEFAULT SERVICE ACCOUNT (Cloud Run):
#    - Automatically uses Cloud Run's default service account
#    - No additional configuration needed
#    - Limited permissions by default
# \=============================================================================

# Authentication environment variables
# GOOGLE_APPLICATION_CREDENTIALS: Path to service account key file (optional)
# GOOGLE_CLOUD_PROJECT: GCP project ID (optional, can be detected from metadata)
ENV GOOGLE_APPLICATION_CREDENTIALS="" \
    GOOGLE_CLOUD_PROJECT="" \
    GCLOUD_PROJECT=""

# Copy Google Cloud SDK from the official image
COPY --from=gcloud /google-cloud-sdk /google-cloud-sdk

# Install system dependencies
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Add Google Cloud SDK to PATH
ENV PATH="/google-cloud-sdk/bin:${PATH}"

# \=============================================================================
# AUTHENTICATION DIRECTORIES AND PERMISSIONS SETUP
# \=============================================================================
# Create directories for various authentication methods with proper permissions

# Create gcloud configuration directory for Application Default Credentials
RUN mkdir -p /home/wagtail/.config/gcloud && \
    chown wagtail:wagtail /home/wagtail/.config/gcloud && \
    chmod 700 /home/wagtail/.config/gcloud

# Create service account key directory for mounted key files
# This directory will be used when GOOGLE_APPLICATION_CREDENTIALS points to a mounted key file
RUN mkdir -p /etc/gcp/service-account && \
    chown wagtail:wagtail /etc/gcp/service-account && \
    chmod 700 /etc/gcp/service-account

# Create alternative service account directory in user space
# Provides flexibility for different mounting strategies
RUN mkdir -p /home/wagtail/.gcp/service-account && \
    chown wagtail:wagtail /home/wagtail/.gcp/service-account && \
    chmod 700 /home/wagtail/.gcp/service-account

# Create gcloud cache and logs directories to avoid permission issues
RUN mkdir -p /home/wagtail/.cache/gcloud && \
    mkdir -p /home/wagtail/.config/gcloud/logs && \
    chown -R wagtail:wagtail /home/wagtail/.cache && \
    chown -R wagtail:wagtail /home/wagtail/.config/gcloud/logs && \
    chmod -R 755 /home/wagtail/.cache && \
    chmod -R 755 /home/wagtail/.config/gcloud/logs

# Installs: Django, Wagtail, psycopg2, gunicorn, etc.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copies your Django app code
COPY --chown=wagtail:wagtail . .

# Creates /tmp/certs directory (writable by wagtail user) for SSL certificates
# This directory is used by entrypoint.sh to store certificates downloaded from Secret Manager
RUN mkdir -p /tmp/certs && \
    chown wagtail:wagtail /tmp/certs && \
    chmod 700 /tmp/certs

# Makes scripts executable
RUN chmod +x ./entrypoint.sh ./start.sh

# Switch to non-root user
# After this point, all operations run as the wagtail user
USER wagtail

# \=============================================================================
# AUTHENTICATION VERIFICATION AND SETUP
# \=============================================================================
# Set up gcloud configuration for the wagtail user
# This ensures gcloud commands work properly regardless of authentication method

# Initialize gcloud configuration (this creates necessary config files)
# The --quiet flag prevents interactive prompts
RUN gcloud config configurations create default --quiet || true && \
    gcloud config set core/disable_usage_reporting true --quiet && \
    gcloud config set component_manager/disable_update_check true --quiet

# Verify gcloud installation and show authentication status
# This helps with debugging authentication issues during container startup
RUN gcloud --version && \
    echo "Gcloud SDK installed and configured successfully"

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=5)" || exit 1

# Expose port 8080 (Cloud Run default)

EXPOSE 8080


# Runtime command: Use startup script
ENTRYPOINT ["./entrypoint.sh"]