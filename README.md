# prabuddh.in

Personal blog. Wagtail runs as a headless CMS (admin and REST API, in `backend/`) and a Nuxt 4 site (server-side rendered, in `frontend/`) shows the content. In production one Hetzner VM runs everything with Docker Compose, with Caddy in front for HTTPS.

## Start developing

### With Docker

```sh
docker compose -f docker-compose.dev.yaml up --build
docker compose -f docker-compose.dev.yaml exec backend python manage.py createsuperuser
```

Site at <http://localhost:3000>, admin at <http://localhost:8000/admin/>, and the test inbox that catches the newsletter emails at <http://localhost:8025>. Both servers reload when you edit files. The full walkthrough is in [`docs/local-development.md`](docs/local-development.md).

### With just

Needs [just](https://just.systems), [uv](https://docs.astral.sh/uv/) and Node 24. Run `just` to list all recipes.

```sh
just sync && just migrate && just createsuperuser
just run     # backend on :8000 (one terminal)
just install && just dev   # frontend on :3000 (another terminal)
just worker  # sends newsletter emails (optional, a third terminal)
```

## Production

```sh
just docker-prod   # or: docker compose -f docker-compose.prod.yaml up -d --build
```

Needs `.env` (see `.env.example`) and `backend/.env` (see `backend/.env.example`) on the server. To send the newsletter you also need an email account and the `EMAIL_*` settings: see [`docs/newsletter-production.md`](docs/newsletter-production.md).

## Docs

- [`AGENTS.md`](AGENTS.md): how the project is laid out, the decisions behind it, and the rules for changing it.
- [`docs/local-development.md`](docs/local-development.md): run the project on your machine, set it up, and try the newsletter locally.
- [`docs/newsletter-production.md`](docs/newsletter-production.md): turn on the newsletter in production with a real email address.
- [`docs/versions.md`](docs/versions.md): every version in the stack and why it was chosen.
- `legacy-ui/`: the old site's templates, kept only as a reference for the UI.
