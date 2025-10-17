# Load environment variables from .env if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# --- Project / container settings ---
IMAGE_NAME := gcr.io/$(GCP_PROJECT)/prabuddh-me
SERVICE_NAME := prabuddh-me
REGION := $(CLOUD_RUN_REGION)  # e.g., us-central1
CONTAINER_NAME := prabuddh-me

# --- Default target ---
.DEFAULT_GOAL := help

# --- Help ---
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Local Development Targets:"
	@echo "  dev                   Run Django dev server (dev.py settings)"
	@echo "  migrate-local         Run local database migrations (SQLite or Cloud SQL Proxy)"
	@echo "  makemigrations        Create database migrations"
	@echo "  superuser-local       Create local superuser"
	@echo "  tailwind-build-local  Build Tailwind CSS locally"
	@echo "  test                  Run tests"
	@echo "  check                 Check for Django issues"
	@echo "  collectstatic         Collect static files (production settings)"
	@echo "  shell-local           Open Django shell (local)"
	@echo "  dbshell               Open database shell"
	@echo "  cloudsql-proxy        Start Cloud SQL Proxy for local PostgreSQL access"
	@echo ""
	@echo "Cloud Run / Production Targets:"
	@echo "  build            Build Docker image"
	@echo "  push             Push image to GCP Container Registry"
	@echo "  deploy           Build, push, deploy, run migrations & superuser on Cloud Run"
	@echo "  deploy-cloudbuild Deploy using Cloud Build (CI/CD)"
	@echo "  tailwind-build   Build Tailwind CSS inside container"
	@echo "  shell            Open Django shell inside container"
	@echo "  logs             Show Cloud Run logs"
	@echo "  stop             Delete Cloud Run service"
	@echo "  clean            Remove local Docker image and Python cache files"
	@echo ""
	@echo "Secret Manager Targets:"
	@echo "  secret-upload      Upload all .env variables to Secret Manager"
	@echo "  secret-update      Update existing secrets in Secret Manager"
	@echo "  secret-list        List all secrets in Secret Manager"
	@echo "  secret-delete-all  Delete all secrets (use with caution!)"
	@echo ""
	@echo "Environment Variables (from .env):"
	@echo "  Required for local dev:"
	@echo "    - DEBUG=true (default)"
	@echo "    - USE_CLOUD_SQL_PROXY=false (default, set true to use Cloud SQL locally)"
	@echo "  Required for production:"
	@echo "    - SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST"
	@echo "    - GS_BUCKET_NAME, GCP_PROJECT"
	@echo "    - ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS"
	@echo "    - WAGTAILADMIN_BASE_URL"

# --- Local Development ---
.PHONY: dev
dev:
	@echo "Starting Django + Tailwind development servers..."
	@DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py tailwind dev

.PHONY: migrate-local
migrate-local:
	@echo "Running migrations locally (SQLite unless USE_CLOUD_SQL_PROXY=true)..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py migrate

.PHONY: makemigrations
makemigrations:
	@echo "Creating new migrations..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py makemigrations

.PHONY: superuser-local
superuser-local:
	@echo "Creating superuser locally..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py createsuperuser

.PHONY: test
test:
	@echo "Running tests..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py test

.PHONY: check
check:
	@echo "Running Django system checks..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py check

.PHONY: collectstatic
collectstatic:
	@echo "Collecting static files (uses production settings)..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production python manage.py collectstatic --noinput

.PHONY: shell-local
shell-local:
	@echo "Opening Django shell (dev settings)..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py shell

.PHONY: dbshell
dbshell:
	@echo "Opening database shell..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py dbshell

.PHONY: tailwind-build-local
tailwind-build-local:
	@echo "Building Tailwind CSS locally..."
	DJANGO_SETTINGS_MODULE=prabuddh_me.settings.dev python manage.py tailwind build

.PHONY: cloudsql-proxy
cloudsql-proxy:
	@echo "Starting Cloud SQL Proxy for local development..."
	@echo "Make sure USE_CLOUD_SQL_PROXY=true in your .env"
	cloud-sql-proxy --port 5432 $(CLOUD_SQL_CONNECTION_NAME)

# --- Docker / Cloud Run ---
.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .

.PHONY: push
push:
	docker push $(IMAGE_NAME)

# Deploy: build, push, deploy, migrate, create superuser
.PHONY: deploy
deploy: build push
	@echo "Deploying $(SERVICE_NAME) to Cloud Run (production settings)..."
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE_NAME) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--set-env-vars DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production \
		--set-env-vars SECRET_KEY=$(SECRET_KEY) \
		--set-env-vars DB_NAME=$(DB_NAME) \
		--set-env-vars DB_USER=$(DB_USER) \
		--set-env-vars DB_PASSWORD=$(DB_PASSWORD) \
		--set-env-vars DB_HOST=$(DB_HOST) \
		--set-env-vars GS_BUCKET_NAME=$(GS_BUCKET_NAME) \
		--set-env-vars GCP_PROJECT=$(GCP_PROJECT) \
		--set-env-vars ALLOWED_HOSTS=$(ALLOWED_HOSTS) \
		--set-env-vars CSRF_TRUSTED_ORIGINS=$(CSRF_TRUSTED_ORIGINS) \
		--set-env-vars WAGTAILADMIN_BASE_URL=$(WAGTAILADMIN_BASE_URL) \
		--add-cloudsql-instances $(CLOUD_SQL_CONNECTION_NAME) \
		--memory 1Gi \
		--port 8080
	@echo "Waiting 10 seconds for service to become available..."
	sleep 10
	@echo "Running migrations..."
	gcloud run jobs execute migrate-job --image $(IMAGE_NAME) --region $(REGION)
	@echo "Creating superuser if not exists..."
	gcloud run jobs execute superuser-job --image $(IMAGE_NAME) --region $(REGION)
	@echo "Deployment complete!"

# Deploy using Cloud Build (recommended for CI/CD)
.PHONY: deploy-cloudbuild
deploy-cloudbuild:
	@echo "Deploying using Cloud Build (production settings)..."
	@echo "Note: Ensure these secrets are set in Secret Manager:"
	@echo "  - SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST"
	@echo "  - GS_BUCKET_NAME, GCP_PROJECT"
	@echo "  - ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, WAGTAILADMIN_BASE_URL"
	gcloud builds submit --config cloudbuild.yaml
	@echo "Cloud Build deployment complete!"

.PHONY: tailwind-build
tailwind-build:
	@echo "Building Tailwind CSS inside container (production settings)..."
	docker run --rm -it \
		--env-file .env \
		-e DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production \
		$(IMAGE_NAME) \
		python manage.py tailwind build

.PHONY: shell
shell:
	@echo "Opening Django shell inside container (production settings)..."
	docker run --rm -it \
		--env-file .env \
		-e DJANGO_SETTINGS_MODULE=prabuddh_me.settings.production \
		$(IMAGE_NAME) \
		python manage.py shell

.PHONY: logs
logs:
	gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$(SERVICE_NAME)" --project $(GCP_PROJECT) --limit 50 --format=json

.PHONY: stop
stop:
	gcloud run services delete $(SERVICE_NAME) --region $(REGION) --platform managed

.PHONY: clean
clean:
	docker rmi $(IMAGE_NAME) || true
	find . -path "./venv" -prune -o -name "*.pyc" -delete
	find . -path "./venv" -prune -o -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# --- Secret Manager ---
.PHONY: secret-upload
secret-upload:
	@echo "Uploading .env variables to Google Secret Manager..."
	@while IFS='=' read -r key value; do \
		if [ ! -z "$$key" ] && [ "$${key:0:1}" != "#" ]; then \
			cleaned_key=$$(echo "$$key" | xargs); \
			cleaned_value=$$(echo "$$value" | sed 's/#.*//' | xargs); \
			if [ ! -z "$$cleaned_value" ]; then \
				echo "Uploading $$cleaned_key..."; \
				echo -n "$$cleaned_value" | gcloud secrets create "$$cleaned_key" \
					--project=$(GCP_PROJECT) \
					--data-file=- \
					--replication-policy="automatic" 2>/dev/null || \
				echo -n "$$cleaned_value" | gcloud secrets versions add "$$cleaned_key" \
					--project=$(GCP_PROJECT) \
					--data-file=-; \
			fi \
		fi \
	done < .env
	@echo "✓ All secrets uploaded successfully"

.PHONY: secret-update
secret-update:
	@echo "Updating .env variables in Google Secret Manager..."
	@while IFS='=' read -r key value; do \
		if [ ! -z "$$key" ] && [ "$${key:0:1}" != "#" ]; then \
			cleaned_key=$$(echo "$$key" | xargs); \
			cleaned_value=$$(echo "$$value" | sed 's/#.*//' | xargs); \
			if [ ! -z "$$cleaned_value" ]; then \
				echo "Updating $$cleaned_key..."; \
				echo -n "$$cleaned_value" | gcloud secrets versions add "$$cleaned_key" \
					--project=$(GCP_PROJECT) \
					--data-file=-; \
			fi \
		fi \
	done < .env
	@echo "✓ All secrets updated successfully"

.PHONY: secret-list
secret-list:
	@gcloud secrets list --project=$(GCP_PROJECT)

.PHONY: secret-delete-all
secret-delete-all:
	@echo "⚠️  This will delete ALL secrets in the project!"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		gcloud secrets list --project=$(GCP_PROJECT) --format="value(name)" | \
		xargs -I {} gcloud secrets delete {} --project=$(GCP_PROJECT) --quiet; \
		echo "✓ All secrets deleted"; \
	else \
		echo "Cancelled"; \
	fi
