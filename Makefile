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
	@echo "  dev                   Run Django dev server"
	@echo "  migrate-local         Run local database migrations"
	@echo "  superuser-local       Create local superuser"
	@echo "  tailwind-build-local  Build Tailwind CSS locally"
	@echo ""
	@echo "Cloud Run / Production Targets:"
	@echo "  build            Build Docker image"
	@echo "  push             Push image to GCP Container Registry"
	@echo "  deploy           Build, push, deploy, run migrations & superuser on Cloud Run"
	@echo "  tailwind-build   Build Tailwind CSS inside container"
	@echo "  shell            Open Django shell inside container"
	@echo "  logs             Show Cloud Run logs"
	@echo "  stop             Delete Cloud Run service"
	@echo "  clean            Remove local Docker image"

# --- Local Development ---
.PHONY: dev
dev:
	python manage.py runserver 0.0.0.0:8000

.PHONY: migrate-local
migrate-local:
	python manage.py migrate

.PHONY: superuser-local
superuser-local:
	python manage.py createsuperuser

.PHONY: tailwind-build-local
tailwind-build-local:
	python manage.py tailwind build

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
	@echo "Deploying $(SERVICE_NAME) to Cloud Run..."
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE_NAME) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--update-env-vars-file .env \
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

.PHONY: tailwind-build
tailwind-build:
	docker run --rm -it \
		--env-file .env \
		$(IMAGE_NAME) \
		python manage.py tailwind build

.PHONY: shell
shell:
	docker run --rm -it \
		--env-file .env \
		$(IMAGE_NAME) \
		python manage.py shell

.PHONY: logs
logs:
	gcloud logs read --project $(GCP_PROJECT) --limit 50 --sort-by timestamp

.PHONY: stop
stop:
	gcloud run services delete $(SERVICE_NAME) --region $(REGION) --platform managed

.PHONY: clean
clean:
	docker rmi $(IMAGE_NAME) || true
