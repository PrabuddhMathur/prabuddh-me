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



# Installs: Django, Wagtail, psycopg2, gunicorn, etc.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copies your Django app code
COPY --chown=wagtail:wagtail . .

# Creates /tmp/certs directory (writable by wagtail user)
RUN mkdir -p /tmp/certs && chown wagtail:wagtail /tmp/certs

# Makes scripts executable
RUN chmod +x ./entrypoint.sh ./start.sh

# Switch to non-root user

USER wagtail


# Health check for Cloud Run

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \

    CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=5)" || exit 1



# Expose port 8080 (Cloud Run default)

EXPOSE 8080


# Runtime command: Use startup script

ENTRYPOINT ["./entrypoint.sh"]