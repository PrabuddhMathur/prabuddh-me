# Base image: Python 3.12 slim
FROM python:3.12-slim-bookworm

# Create non-root user early
RUN useradd --create-home --shell /bin/bash wagtail

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
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

# Create writable directories
RUN mkdir -p /app/media /app/staticfiles && chown -R wagtail:wagtail /app

# Switch to non-root user
USER wagtail

# Expose port
EXPOSE 8000

# Runtime command
CMD ["./start.sh"]
