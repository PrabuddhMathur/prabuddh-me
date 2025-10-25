#!/bin/bash
set -e                                  # Exit if any command fails

echo "Starting mTLS setup..."

# Create writable directory for certificates
mkdir -p /tmp/certs
chmod 700 /tmp/certs                    # Only owner can read/write/execute

# Copy certificates from read-only mounts to writable location
# Source: /var/secrets/* (mounted by Cloud Run from Secret Manager)
# Destination: /tmp/certs/* (writable filesystem)

cp /var/secrets/db-client-key/db-client-key /tmp/certs/client.key
chmod 600 /tmp/certs/client.key         # Only owner can read/write

cp /var/secrets/db-client-cert/db-client-cert /tmp/certs/client.crt
chmod 644 /tmp/certs/client.crt         # Owner: read/write, Others: read

cp /var/secrets/db-ca-cert/db-ca-cert /tmp/certs/ca.crt
chmod 644 /tmp/certs/ca.crt

# Set environment variables for Django to use
export DB_SSLKEY=/tmp/certs/client.key
export DB_SSLCERT=/tmp/certs/client.crt
export DB_SSLROOTCERT=/tmp/certs/ca.crt

echo "Certificates ready. Starting Django..."

# Execute start.sh (replaces this process)
exec ./start.sh