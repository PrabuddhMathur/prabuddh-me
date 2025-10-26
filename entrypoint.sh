#!/bin/bash
set -e

# Enable logging with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ENTRYPOINT: $1"
}

log "Starting entrypoint script..."

# Use /tmp/certs directory (already created and owned by wagtail in Dockerfile)
log "Using certificate directory at /tmp/certs..."

# Download SSL certificates from Google Cloud Secret Manager
log "Downloading SSL certificates from Google Cloud Secret Manager..."

log "Downloading client certificate..."
if gcloud secrets versions access latest --secret=db-client-cert > /tmp/certs/client.crt; then
    log "Client certificate downloaded successfully"
else
    log "ERROR: Failed to download client certificate"
    exit 1
fi

log "Downloading client key..."
if gcloud secrets versions access latest --secret=db-client-key > /tmp/certs/client.key; then
    log "Client key downloaded successfully"
else
    log "ERROR: Failed to download client key"
    exit 1
fi

log "Downloading server CA certificate..."
if gcloud secrets versions access latest --secret=db-server-ca > /tmp/certs/ca.crt; then
    log "Server CA certificate downloaded successfully"
else
    log "ERROR: Failed to download server CA certificate"
    exit 1
fi

# Set proper permissions for certificate files
log "Setting secure permissions for certificate files..."
chmod 600 /tmp/certs/client.key
chmod 644 /tmp/certs/client.crt /tmp/certs/ca.crt
log "Certificate permissions set successfully"

# Export paths for Django
log "Setting SSL certificate environment variables..."
export DB_SSLCERT=/tmp/certs/client.crt
export DB_SSLKEY=/tmp/certs/client.key
export DB_SSLROOTCERT=/tmp/certs/ca.crt
log "Environment variables set:"
log "  DB_SSLCERT=${DB_SSLCERT}"
log "  DB_SSLKEY=${DB_SSLKEY}"
log "  DB_SSLROOTCERT=${DB_SSLROOTCERT}"

log "SSL certificates ready. Handing off to start.sh..."

# Execute start.sh (replaces this process)
exec ./start.sh