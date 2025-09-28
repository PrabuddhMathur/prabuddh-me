# Base image: Python 3.12 slim
FROM python:3.12-slim-bookworm

# Create non-root user
RUN useradd wagtail

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production

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

# Make startup script executable
RUN chmod +x start.sh

# Create media directory for file storage fallback
RUN mkdir -p /app/media && chown wagtail:wagtail /app/media

# Ensure non-root user owns files
RUN chown -R wagtail:wagtail /app

# Ensure non-root user owns files
RUN chown -R wagtail:wagtail /app

# Switch to non-root user
USER wagtail

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Runtime command: Use startup script
CMD ["./start.sh"]
