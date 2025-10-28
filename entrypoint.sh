#!/bin/bash
set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ENTRYPOINT: $1"
}

log "Starting entrypoint script..."

# Check required env var
if [ -z "$GCP_PROJECT" ]; then
    log "ERROR: GCP_PROJECT environment variable is not set"
    exit 1
fi

# --- Prepare writable temp directory for certs ---
echo "[ENTRYPOINT] Ensuring /tmp/certs exists..."
mkdir -p /tmp/certs

log "Fetching secrets via Secret Manager API (Python)..."

# Use Python script to fetch secrets and set file permissions
python <<'EOF'
import os
from google.cloud import secretmanager

project_id = os.environ.get("GCP_PROJECT")
secrets = {
    "db-client-cert": "/tmp/certs/client.crt",
    "db-client-key": "/tmp/certs/client.key",
    "db-server-ca": "/tmp/certs/ca.crt",
}

client = secretmanager.SecretManagerServiceClient()

for secret_name, path in secrets.items():
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    print(f"[SecretManager] Downloading {secret_name} → {path}")
    response = client.access_secret_version(name=name)
    with open(path, "wb") as f:
        f.write(response.payload.data)
    # Strict permissions for key, normal for others
    if path.endswith(".key"):
        os.chmod(path, 0o600)
    else:
        os.chmod(path, 0o644)

print("[SecretManager] All certificates downloaded successfully.")
EOF

# Export environment variables for Django/Postgres
export DB_SSLCERT=/tmp/certs/client.crt
export DB_SSLKEY=/tmp/certs/client.key
export DB_SSLROOTCERT=/tmp/certs/ca.crt

log "SSL certificates ready. Handing off to start.sh..."
exec ./start.sh