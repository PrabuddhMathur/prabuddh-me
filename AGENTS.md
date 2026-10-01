# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Cursor and others) working in this repository.

## Git and attribution

- **Never credit an AI tool as an author or contributor.** No `Co-Authored-By:` trailers for any AI, and no "Generated with …" lines in commit messages, PR titles, PR descriptions or code comments. Commits and PRs are authored by the repository owner only.
- Commit or push only when asked. Do work on a branch, not `main`.

## Project

Personal blog for prabuddh.in, rebuilt from scratch starting 2026-10-01.

| Path | What it is |
|---|---|
| `backend/` | Wagtail as a headless CMS: admin and REST API only, no server-rendered pages. Django 5.2 LTS, Wagtail 7.4 LTS, Python 3.14, managed with uv. SQLite database. |
| `frontend/` | Nuxt 4 with server-side rendering (not SPA mode) and Tailwind CSS 4 (no daisyUI). |
| `docs/versions.md` | The single source of truth for every version in the stack and why it was chosen. Update it whenever a version changes. |
| `docs/local-development.md` | How to run the project locally (Docker or not), set it up and try the newsletter. |
| `docs/newsletter-production.md` | How to turn on the newsletter in production with a real email address. |
| `justfile` | Task runner (`just` lists the recipes): backend, frontend and Docker commands. |
| `legacy-ui/` | The old site's templates, CSS and JS, restored from commit `49cda9c`. Reference only: never import from it or ship it. |

## Decisions (ask before changing any of these)

- **The UI must look exactly like the old site.** Port templates from `legacy-ui/` to Vue components faithfully. Replace daisyUI classes with plain Tailwind using the same colour values; `legacy-ui/theme/static/css/dist/styles.css` has the exact theme colours. The two themes are `light` and `dim`.
- **Production:** one Hetzner VM running Docker Compose, with Caddy in front for automatic HTTPS. Everything is served from one domain. Caddy sends `/admin/`, `/api/`, `/documents/` and `/static/` to Wagtail, serves `/media/` directly from the uploads volume (Django doesn't serve media in production), and sends everything else to Nuxt. No CORS setup is needed. Caddy also sets `X-Real-IP`, which the newsletter signup throttle reads as the visitor's address.
- **Docker:** all Docker files live together at the root. `docker/Dockerfile.dev` and `docker/Dockerfile.prod` each have a `backend` and a `frontend` target, and the build context is the repository root. `docker-compose.dev.yaml` runs both dev servers with live reload, the newsletter `worker` and Mailpit (a local inbox that catches every email, at `http://localhost:8025`); `docker-compose.prod.yaml` adds Caddy (`docker/Caddyfile`) and the `worker`. Base image tags must match across both Dockerfiles and `docs/versions.md`.
- **Internal traffic:** in Docker, the Nuxt server calls the backend directly at `http://backend:8000` (`NUXT_BACKEND_URL`). That's why production `ALLOWED_HOSTS` includes `backend` and Django's own HTTPS redirect is off (Caddy does the redirect).
- **Task runner:** `just`. No Makefile.
- **Configuration:** `django-environ`. Secrets live only in environment variables or `.env` files, which are never committed. Each app keeps a `.env.example` up to date.
- **Database:** SQLite in WAL mode with `IMMEDIATE` transactions and a busy timeout. Never back it up by copying the live file; use SQLite's backup command.
- **TypeScript:** pinned to 6.0.x, because `vue-tsc` doesn't support TypeScript 7 yet.
- **Versions:** prefer LTS lines. Manifests (`pyproject.toml`, `package.json`) pin the version line and lockfiles pin exact versions.

## Working rules

- Before deleting more than a couple of files, list them and get confirmation, especially anything that could still serve as reference.
- Keep it simple. One person maintains this and may not touch it for months, so fewer moving parts beats cleverness.

## Backend

Layout:

- `config/settings/`: `base.py` (shared), `dev.py` (default for `manage.py`), `production.py`. Environment-specific values come from env vars; `backend/.env.example` lists them all.
- `config/urls.py`: the plain JSON endpoints `/api/v2/site/`, `/api/v2/posts/` and `/api/v2/search/`, listed before the Wagtail router so they win over `/api/v2/`.
- `config/api.py`: the Wagtail REST API (v2) router: `pages` (its `/find/` returns the page instead of redirecting), `images`, and the `page_preview` endpoint used by the frontend's `/preview` page.
- `core/`: shared code. `SEOFields` mixin, `StaticPage`, the site settings (`SiteSettings`, `HeaderSettings`, `FooterSettings`, `AuthorSettings`, edited under Settings in the admin), the StreamField blocks (`blocks.py`), serializers, the spoiler rich-text feature (`wagtail_hooks.py`), and the `site` and `search` views.
- `blog/`: `BlogPage` (a post; its public URL is `/YYYY/MM/DD/slug/`, built in `get_url_parts`), the `posts` view (listing, tag and date filters, 12 per page) and the management command `recalculate_reading_times [--dry-run]`.
- `newsletter/`: the double opt-in newsletter. Models `Subscriber`, `Issue` (one emailed post, "Sent posts" in the admin) and `Delivery` (one issue to one subscriber); the public endpoints `/api/v2/newsletter/subscribe/`, `confirm/` and `unsubscribe/` (`views.py`, registered in `config/urls.py`); the emails (`emails.py`, templates in `templates/newsletter/emails/`); the queue (`sending.py`); the Wagtail admin (`wagtail_hooks.py`, `admin_views.py`: Newsletter menu, "Email subscribers" on live posts); and the deploy check `newsletter.W001`. `manage.py newsletter_worker [--once] [--reload]` sends the queue in the background. It runs as the `worker` service in both compose files and shares the backend's database and media volumes. Only the worker sends post emails; confirmation emails go out from the web request.
- `home/`: the `HomePage` model.
- `data/`: the SQLite database. Git-ignored apart from `.gitkeep`.

Rules:

- Every page model must include `HeadlessMixin` (from `wagtail_headless_preview.models`), so previews and "View live" go to the Nuxt frontend.
- Expose fields to the frontend with `api_fields` on the page model.
- Email settings (`EMAIL_*`, `DEFAULT_FROM_EMAIL`, `NEWSLETTER_*`) come from env vars, listed in `backend/.env.example`. Links in emails are built from `FRONTEND_URL`. Dev settings default to the console email backend; the dev compose points it at Mailpit.
- A new StreamField block needs a matching Vue component in `frontend/app/components/blocks/`.
- The frontend types the API responses by hand in `frontend/app/types/api.ts`. Change both together.

Commands, run from `backend/`:

| Command | What it does |
|---|---|
| `uv sync` | Install dependencies from `uv.lock` |
| `uv run manage.py migrate` | Apply database migrations |
| `uv run manage.py createsuperuser` | Create an admin login |
| `uv run manage.py runserver` | Dev server: admin at `http://localhost:8000/admin/`, API at `/api/v2/pages/` |
| `uv run manage.py test` | Run the tests (`core/tests.py`, `blog/tests.py`, `newsletter/tests.py`) |
| `uv run manage.py newsletter_worker --reload` | Send queued newsletter emails (`just worker`) |
| `uv run manage.py makemigrations --check --dry-run` | Fails if a model change has no migration |
| `uv run ruff format . && uv run ruff check .` | Format and lint |
| `uv run manage.py check --deploy --settings=config.settings.production` | Production checklist (needs the production env vars) |

## Frontend

Nuxt 4 with SSR, in `frontend/app/` (Nuxt 4 layout, so source is under `app/`).

- `pages/` (file-based routes; `[x]` is a parameter, `[...slug]` a catch-all):
  - `index.vue` (home page), `blog/index.vue` (listing), `blog/tag/[tag].vue`
  - `[year]/index.vue`, `[year]/[month]/index.vue`, `[year]/[month]/[day]/index.vue` (date archives) and `[year]/[month]/[day]/[slug].vue` (a post)
  - `newsletter/index.vue`, `newsletter/confirm.vue`, `newsletter/unsubscribe.vue` (the newsletter's landing, confirm and unsubscribe pages; the footer signup is `components/site/NewsletterSignup.vue`)
  - `search.vue`, `preview.vue` (Wagtail preview and "View live" target), `[...slug].vue` (static pages such as `/about/`; a post's `/<slug>/` redirects to its date URL)
- `components/`, grouped by folder for tidiness but used by file name only (`<PostCard>`), so every file name must be unique: `article/` (post page, image gallery), `blocks/` (one component per StreamField block, plus `StreamField.vue` that picks by block type), `content/` (`RichText`), `home/`, `listing/` (cards, list items, pagination), `page/`, `post/` (meta, tags, social links), `site/` (header, footer, mobile menu, newsletter, theme toggle), `ui/`.
- `composables/`: `useApi` (`useFetch` against the backend), `useSiteSettings` (header, footer and author, fetched once), `usePageSeo` (title, description, Open Graph, canonical).
- `utils/`: `format.ts` (dates and text, matching the old Django template filters), `urls.ts` (internal links, `absoluteUrl`, renditions), `gallery.ts`. `types/api.ts` holds the API response types. `layouts/default.vue`, `error.vue` and `app.vue` wrap the pages.

Data flow:

- `plugins/api.ts` provides `$api`. On the Nuxt server it calls the backend directly at `NUXT_BACKEND_URL` (default `http://localhost:8000`, `http://backend:8000` in Docker). In the browser it calls same-origin `/api/...`: Caddy routes it to Wagtail in production, Nuxt's dev proxy (`routeRules` in `nuxt.config.ts`) does in development, which is also why no CORS setup is needed. `/media/` and `/documents/` work the same way.
- Pages use `useApi('/api/v2/...')`. Wagtail's `pages/find/?html_path=` fetches a page by URL path (home, static pages, posts); `page_preview/` serves drafts. The custom endpoints serve what Wagtail's API has no good shape for: `site/` (settings), `posts/` (listing, `?tag=`, `?year=&month=&day=`, `?page=`) and `search/` (`?query=&page=`).
- `NUXT_PUBLIC_SITE_URL` is the public address used for canonical and Open Graph URLs (set from `DOMAIN` in `docker-compose.prod.yaml`). See `frontend/.env.example`.

Theming:

- Two themes, `light` and `dim`, as in the old site. `@nuxtjs/color-mode` keeps the choice in localStorage under `theme` and sets `<html data-theme="...">` (same key and values as the old site, so returning visitors keep theirs). `plugins/theme.server.ts` renders `light` on the server.
- Tailwind CSS 4, configured in `assets/css/main.css` (no daisyUI, no `tailwind.config`). Colour tokens in `@theme` keep daisyUI's names (`bg-base-100`, `text-base-content/60`, `border-primary`) with the old site's values; the dim values override them under `[data-theme="dim"]`. Use `dim:` to style the dim theme only.

Rules:

- Templates were ported from `legacy-ui/` and must keep matching it exactly (markup, classes, spacing, whitespace). Compare against the old template before changing any component. `nuxt.config.ts` has settings that exist only for this (`vue.compilerOptions.whitespace: 'preserve'`, `postcss.plugins.cssnano: false`); don't remove them.
- The dev Docker container writes `frontend/.nuxt` through the bind mount. Stop it (`just docker-dev-down`) before running `npm run typecheck` or `npm run build` on the host.

Commands, run from `frontend/` (or use the `just` recipes of the same name, from the root):

| Command | What it does |
|---|---|
| `npm ci` | Install dependencies from `package-lock.json` (`just install`) |
| `npm run dev` | Dev server at `http://localhost:3000`; needs the backend running on `:8000` (`just dev`) |
| `npm run typecheck` | Type-check with `vue-tsc` (`just typecheck`) |
| `npm run build` | Production build into `.output/` (`just build`) |
| `npm run preview` | Run the production build locally |

## Docker

Run from the repository root (`just docker-dev`, `docker-dev-down`, `docker-manage <command>` and `docker-prod` wrap these):

| Command | What it does |
|---|---|
| `docker compose -f docker-compose.dev.yaml up --build` | Dev: admin at `http://localhost:8000/admin/`, site at `http://localhost:3000`, test inbox (Mailpit) at `http://localhost:8025`. Add `-V` after changing frontend dependencies |
| `docker compose -f docker-compose.dev.yaml exec backend python manage.py <command>` | Run a Django command in the dev container (e.g. `createsuperuser`, `makemigrations`) |
| `docker compose -f docker-compose.prod.yaml up -d --build` | Production. Needs `.env` (`DOMAIN`) and `backend/.env` |

The dev database lives in the `backend_data` Docker volume, separate from `backend/data/` used when running `uv run manage.py runserver` directly.

The dev frontend container sets `CHOKIDAR_USEPOLLING=true` (read in `frontend/nuxt.config.ts`), because bind-mounted folders send no file-change events and the dev server would otherwise miss new and edited files until restarted.
