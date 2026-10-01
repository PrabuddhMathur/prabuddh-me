# Task runner (https://just.systems). Run `just` to list recipes.
# Backend and frontend recipes run on the host; the docker recipes run the Compose stacks.

# List the recipes
default:
    @just --list

# --- Backend (uv, run from backend/) ---

# Install backend dependencies from uv.lock
[working-directory: 'backend']
sync:
    uv sync

# Apply database migrations
[working-directory: 'backend']
migrate:
    uv run manage.py migrate

# Start the Wagtail dev server on :8000
[working-directory: 'backend']
run:
    uv run manage.py runserver

# Create an admin login
[working-directory: 'backend']
createsuperuser:
    uv run manage.py createsuperuser

# Run the backend tests
[working-directory: 'backend']
test:
    uv run manage.py test

# Format and lint the backend
[working-directory: 'backend']
lint:
    uv run ruff format .
    uv run ruff check .

# Fail if a model change has no migration
[working-directory: 'backend']
makemigrations-check:
    uv run manage.py makemigrations --check --dry-run

# Send queued newsletter emails (restarts on code changes)
[working-directory: 'backend']
worker:
    uv run manage.py newsletter_worker --reload

# Recalculate every post's reading time (add --dry-run to preview)
[working-directory: 'backend']
reading-times *args:
    uv run manage.py recalculate_reading_times {{args}}

# --- Frontend (npm, run from frontend/) ---

# Install frontend dependencies from package-lock.json
[working-directory: 'frontend']
install:
    npm ci

# Start the Nuxt dev server on :3000
[working-directory: 'frontend']
dev:
    npm run dev

# Build the Nuxt server for production
[working-directory: 'frontend']
build:
    npm run build

# Type-check the Vue and TypeScript code
[working-directory: 'frontend']
typecheck:
    npm run typecheck

# --- Docker (from the repository root) ---

# Start only Mailpit, the local inbox (SMTP :1025, inbox :8025), for `just run` without the full stack
mailpit:
    docker compose -f docker-compose.dev.yaml up mailpit

# Start the dev stack with live reload (site :3000, admin :8000, inbox :8025)
docker-dev:
    docker compose -f docker-compose.dev.yaml up --build

# Stop the dev stack (its database volume is kept)
docker-dev-down:
    docker compose -f docker-compose.dev.yaml down

# Run a Django command in the dev backend container, e.g. `just docker-manage createsuperuser`
docker-manage *args:
    docker compose -f docker-compose.dev.yaml exec backend python manage.py {{args}}

# Build and start production (needs .env and backend/.env)
docker-prod:
    docker compose -f docker-compose.prod.yaml up -d --build
