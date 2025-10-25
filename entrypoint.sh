#!/bin/bash

echo "Starting up container..."

# Check if the secret file exists before trying to change permissions
if [ -f "/var/secrets/db-client-key/db-client-key" ]; then
  echo "Setting secure permissions for db-client-key..."
  chmod 600 "/var/secrets/db-client-key/db-client-key"
fi

# Add similar checks for other files if needed
if [ -f "/var/secrets/db-ca-cert/db-ca-cert" ]; then
  echo "Setting permissions for db-ca-cert..."
  chmod 644 "/var/secrets/db-ca-cert/db-ca-cert"
fi

# Execute the main application command (your start.sh)
exec "./start.sh"
