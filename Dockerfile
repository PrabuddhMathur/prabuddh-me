# Base image: Python 3.12 slim
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

# Install system dependencies (keep build deps separate for potential removal)
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files (respects .dockerignore)
COPY --chown=wagtail:wagtail . .

# Make startup script executable
RUN chmod +x start.sh

# Create media directory for file storage fallback
RUN mkdir -p /app/media && chown wagtail:wagtail /app/media

# Fix permissions for SSL certificate files
RUN chmod 600 /var/secrets/db-client-key/db-client-key && \
    chmod 644 /var/secrets/db-ca-cert/db-ca-cert && \
    chmod 644 /var/secrets/db-client-cert/db-client-cert

# Switch to non-root user
USER wagtail

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=5)" || exit 1

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Runtime command: Use startup script
CMD ["./start.sh"]
