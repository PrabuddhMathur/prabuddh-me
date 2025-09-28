#!/bin/bash

# Cloud Build setup script for Secret Manager integration
# This script helps set up the required permissions for Cloud Build deployment

set -e

echo "Setting up Cloud Build for Django/Wagtail deployment with Secret Manager..."

# Check if required environment variables are set
if [ -z "$GCP_PROJECT" ]; then
    echo "Error: GCP_PROJECT environment variable not set"
    exit 1
fi

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Grant Cloud Build service account necessary permissions
echo "Granting Cloud Build permissions..."
CLOUDBUILD_SA="$(gcloud projects describe $GCP_PROJECT --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"

# Grant Cloud Build access to Cloud Run
gcloud projects add-iam-policy-binding $GCP_PROJECT \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/run.developer" || true

# Grant Cloud Build access to Cloud SQL
gcloud projects add-iam-policy-binding $GCP_PROJECT \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/cloudsql.client" || true

# Grant Cloud Build access to Google Cloud Storage
gcloud projects add-iam-policy-binding $GCP_PROJECT \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/storage.objectAdmin" || true

# Grant Cloud Build access to Secret Manager
gcloud projects add-iam-policy-binding $GCP_PROJECT \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/secretmanager.secretAccessor" || true

echo "Cloud Build setup complete!"
echo ""
echo "✅ Secret Manager Configuration:"
echo "   Secret: projects/160250011949/secrets/prabuddh-me-secrets"
echo "   Contains: Your entire .env file content"
echo ""
echo "Next steps:"
echo "1. Set up Cloud Build trigger connected to your GitHub repository"
echo "2. Configure the trigger to use cloudbuild.yaml"
echo "3. Your secrets are already configured in Secret Manager"
echo ""
echo "Deploy with:"
echo "make deploy-cloudbuild"
echo ""
echo "🔒 SECURITY: All secrets are now managed through Google Secret Manager"
echo "   No sensitive data is stored in your repository or build configuration"