# --- Default target ---
.DEFAULT_GOAL := help

# --- Help ---
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development (Local) Targets:"
	@echo "  dev                   Start dev environment with Docker Compose"
	@echo "  dev-build             Build dev containers"
	@echo "  dev-down              Stop dev environment"
	@echo "  dev-logs              Show dev container logs"
	@echo "  dev-shell             Open Django shell in dev container"
	@echo "  dev-migrate           Run migrations in dev container"
	@echo "  dev-makemigrations    Create migrations in dev container"
	@echo "  dev-superuser         Create superuser in dev container"
	@echo ""
	@echo "Production (Hetzner) Targets:"
	@echo "  prod-build            Build production containers"
	@echo "  prod-up               Start production environment"
	@echo "  prod-down             Stop production environment"
	@echo "  prod-restart          Restart production services"
	@echo "  prod-logs             Show production logs"
	@echo "  prod-shell            Open Django shell in production container"
	@echo "  prod-migrate          Run migrations in production"
	@echo "  prod-collectstatic    Collect static files in production"
	@echo ""
	@echo "Utility Targets:"
	@echo "  clean                 Remove Docker images and Python cache"
	@echo "  prune                 Clean up unused Docker resources"

# =====================================================
# Development Targets
# =====================================================
.PHONY: dev
dev:
	@echo "Starting development environment..."
	docker compose -f compose.yaml -f compose.dev.yaml up

.PHONY: dev-build
dev-build:
	@echo "Building development containers..."
	docker compose -f compose.yaml -f compose.dev.yaml build

.PHONY: dev-down
dev-down:
	@echo "Stopping development environment..."
	docker compose -f compose.yaml -f compose.dev.yaml down

.PHONY: dev-logs
dev-logs:
	docker compose -f compose.yaml -f compose.dev.yaml logs -f

.PHONY: dev-shell
dev-shell:
	@echo "Opening Django shell (dev)..."
	docker compose -f compose.yaml -f compose.dev.yaml exec web python manage.py shell

.PHONY: dev-migrate
dev-migrate:
	@echo "Running migrations (dev)..."
	docker compose -f compose.yaml -f compose.dev.yaml exec web python manage.py migrate

.PHONY: dev-makemigrations
dev-makemigrations:
	@echo "Creating migrations (dev)..."
	docker compose -f compose.yaml -f compose.dev.yaml exec web python manage.py makemigrations

.PHONY: dev-superuser
dev-superuser:
	@echo "Creating superuser (dev)..."
	docker compose -f compose.yaml -f compose.dev.yaml exec web python manage.py createsuperuser

# =====================================================
# Production Targets (Hetzner)
# =====================================================
.PHONY: prod-build
prod-build:
	@echo "Building production containers..."
	docker compose -f compose.yaml -f compose.prod.yaml build

.PHONY: prod-up
prod-up:
	@echo "Starting production environment..."
	docker compose -f compose.yaml -f compose.prod.yaml up -d
	@echo "✓ Production is running!"
	@echo "Check logs with: make prod-logs"

.PHONY: prod-down
prod-down:
	@echo "Stopping production environment..."
	docker compose -f compose.yaml -f compose.prod.yaml down

.PHONY: prod-restart
prod-restart:
	@echo "Restarting production services..."
	docker compose -f compose.yaml -f compose.prod.yaml restart

.PHONY: prod-logs
prod-logs:
	docker compose -f compose.yaml -f compose.prod.yaml logs -f

.PHONY: prod-shell
prod-shell:
	@echo "Opening Django shell (production)..."
	docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py shell

.PHONY: prod-migrate
prod-migrate:
	@echo "Running migrations (production)..."
	docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py migrate

.PHONY: prod-collectstatic
prod-collectstatic:
	@echo "Collecting static files (production)..."
	docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py collectstatic --noinput

# =====================================================
# Utility Targets
# =====================================================
.PHONY: clean
clean:
	@echo "Cleaning up..."
	find . -path "./venv" -prune -o -name "*.pyc" -delete
	find . -path "./venv" -prune -o -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

.PHONY: prune
prune:
	@echo "Pruning unused Docker resources..."
	docker system prune -af --volumes
