# Prabuddh.me - Django/Wagtail Project

A personal website built with Django and Wagtail CMS, deployed on Google Cloud Run with Cloud SQL (PostgreSQL) and Google Cloud Storage.

## Architecture

- **Framework**: Django 5.2 + Wagtail 7.1
- **Database**: Cloud SQL with PostgreSQL 17
- **Static/Media Files**: Google Cloud Storage
- **Hosting**: Google Cloud Run
- **CI/CD**: Google Cloud Build

## Environment Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (for local development)
- Google Cloud CLI
- Docker (for containerization)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd prabuddh-me
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Run the setup script**
   ```bash
   ./setup_local.sh
   ```

4. **Start the development server**
   ```bash
   make dev
   ```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DJANGO_SETTINGS_MODULE`: `prabuddh_me.settings.dev` (local) or `prabuddh_me.settings.production`
- `DEBUG`: `True` for development, `False` for production
- `SECRET_KEY`: Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`: Database connection
- `GS_BUCKET_NAME`: Google Cloud Storage bucket name
- `GCP_PROJECT`: Google Cloud project ID

## Deployment

### Google Cloud Setup

1. **Create Cloud SQL instance**
   ```bash
   gcloud sql instances create prabuddh-me \
     --database-version=POSTGRES_17 \
     --tier=db-f1-micro \
     --region=asia-south1
   ```

2. **Create database**
   ```bash
   gcloud sql databases create prabuddh_me_db \
     --instance=prabuddh-me
   ```

3. **Create GCS bucket**
   ```bash
   gsutil mb gs://prabuddh-me-bucket
   gsutil iam ch allUsers:objectViewer gs://prabuddh-me-bucket
   ```

### Cloud Build Deployment

The project uses Cloud Build for automatic deployment from GitHub:

```bash
# Deploy using Cloud Build
make deploy-cloudbuild

# Or directly
gcloud builds submit --config cloudbuild.yaml
```

**Important**: Before using Cloud Build, you need to:
1. Run the setup script: `./setup_cloudbuild.sh`
2. Update the hardcoded values in `cloudbuild.yaml` with your actual:
   - `SECRET_KEY`
   - `DB_PASSWORD` 
   - `SUPERUSER_PASSWORD`
3. Set up a Cloud Build trigger connected to your GitHub repository

### Makefile Deployment

For manual deployment using the Makefile:

```bash
# Complete deployment (build, push, deploy, migrate)
make deploy

# Individual steps
make build    # Build Docker image
make push     # Push to Container Registry
```

### Manual Cloud Run Deployment

Using the Makefile (recommended):
```bash
# Complete deployment pipeline
make deploy
```

Or using raw gcloud commands:
```bash
# Build and push image
make build
make push

# Deploy to Cloud Run
gcloud run deploy prabuddh-me \
  --image gcr.io/prabuddh-me-5/prabuddh-me \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production \
  --set-env-vars CLOUD_RUN=true \
  --add-cloudsql-instances prabuddh-me-5:asia-south1:prabuddh-me
```

## Settings Configuration

The project uses a modular settings structure:

- `base.py`: Common settings shared across environments
- `dev.py`: Development-specific settings
- `production.py`: Production settings for Cloud Run
- `local.py`: Local overrides (not tracked in git)

### Key Features

- **Environment-based configuration** using `python-decouple`
- **Automatic database detection** (Cloud SQL vs local PostgreSQL)
- **Google Cloud Storage integration** for static/media files
- **Security hardening** for production deployment
- **Comprehensive logging** for Cloud Run

## Database Migrations

```bash
# Create migrations
make makemigrations

# Apply migrations
make migrate-local

# Create superuser
make superuser-local
```

## Static Files

- **Development**: Local file storage with WhiteNoise
- **Production**: Google Cloud Storage

## Monitoring and Logs

View Cloud Run logs:
```bash
# Using Makefile
make logs

# Or directly with gcloud
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=prabuddh-me" --limit=100
```

## Common Commands

### Local Development
```bash
# Run development server
make dev

# Run database migrations
make migrate-local

# Create superuser
make superuser-local

# Build Tailwind CSS
make tailwind-build-local

# Run tests
make test

# Check for issues
make check

# Collect static files
make collectstatic

# Shell access
make shell-local

# Database shell
make dbshell
```

### Production/Cloud Run
```bash
# Deploy to Cloud Run
make deploy

# View logs
make logs

# Shell access (containerized)
make shell

# Build Tailwind in container
make tailwind-build

# Clean local Docker images
make clean

# Stop Cloud Run service
make stop
```

### Available Makefile Targets
```bash
# See all available commands
make help
```

## Troubleshooting

### Cloud SQL Connection Issues
- Ensure Cloud SQL Proxy is running for local development
- Check that the Cloud SQL instance allows connections from Cloud Run
- Verify environment variables are correctly set

### Static Files Not Loading
- Confirm GCS bucket permissions are set correctly
- Check that `GS_BUCKET_NAME` environment variable is set
- Verify GCS credentials are properly configured

### Database Migration Issues
- Run `python manage.py showmigrations` to see migration status
- Use `--fake` flag to mark migrations as applied without running them
- Check database connectivity with `python manage.py dbshell`

## License

MIT License (or your preferred license)

## Contact

[Your contact information]