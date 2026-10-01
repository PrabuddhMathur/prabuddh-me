# Version register

Last researched: **2026-09-30**

**Stack:** Wagtail as a headless CMS (`backend/`) + Nuxt (`frontend/`), Docker Compose on a Hetzner VM, Caddy in front for HTTPS.

## How versions are chosen

- Use the LTS line wherever a project has one (Django, Wagtail, Node.js, Ubuntu).
- Where there is no LTS, use the latest stable release and note its support window.
- Manifests pin the line (e.g. `Django>=5.2.17,<5.3`). Lock files (`uv.lock`, `package-lock.json`) pin exact versions.
- Docker images use exact patch tags. Dependabot proposes updates.

## Runtimes and operating systems

| Component | Version | Track | Supported until | Notes |
|---|---|---|---|---|
| Python | `3.14.7` | 3.14 (no LTS exists) | 2030-10-31 | Bug fixes until 2027-10-01, then security only. [Why](#python-314) |
| Node.js | `24.21.0` | 24 LTS "Krypton" | 2028-04-30 | Node 26 becomes LTS on 2026-10-28. [Why](#nodejs-24) |
| npm | `11.19.0` | Bundled with Node 24 | Same as Node 24 | |
| Debian (container base) | 13 "trixie" | Stable | 2028-08-09 | Debian LTS until 2030-06-30. [Why](#debian-based-images) |
| Ubuntu (Hetzner VM) | `26.04.1` | 26.04 LTS | 2031-05-29 | |

**Pinned in:** Python in `backend/.python-version` and the base image in both `docker/Dockerfile.dev` and `docker/Dockerfile.prod`. Node in `frontend/package.json` (`engines`) and the same two Dockerfiles.

## Backend (Python packages)

| Component | Version | Track | Supported until | Notes |
|---|---|---|---|---|
| Django | `5.2.17` | 5.2 LTS | 2028-04-30 | |
| Wagtail | `7.4.3` | 7.4 LTS | 2027-11-02 | [Why not 8.0](#wagtail-74-lts) |
| `wagtail-headless-preview` | `0.9.0` | Latest | No fixed policy | Lists Wagtail 7 support only |
| `django-environ` | `0.14.0` | Latest | No fixed policy | Reads settings from environment variables |
| `gunicorn` | `26.2.0` | Latest | No fixed policy | |
| `whitenoise` | `6.12.0` | Latest | No fixed policy | |
| `ruff` | `0.16.9` | Latest | No fixed policy | Dev only |
| `uv` | `0.12.21` | Latest | No fixed policy | Tool, not a dependency |

**Pinned in:** `backend/pyproject.toml` (ranges) and `backend/uv.lock` (exact). uv itself is pinned by the uv image tag in both Dockerfiles.

## Database

| Component | Version | Track | Supported until | Notes |
|---|---|---|---|---|
| SQLite | `3.46.1` | 3.x, from Debian 13 | Follows Debian 13 | Comes with the Python base image. [Why](#sqlite) |

**Pinned in:** the backend base image (Debian 13's `libsqlite3`). It only changes when the base image moves to a new Debian release.

## Frontend (npm packages)

| Component | Version | Track | Supported until | Notes |
|---|---|---|---|---|
| Nuxt | `4.5.2` | 4.x | No fixed EOL | No LTS. Nuxt 3 reached end of life on 2026-07-31 |
| Vue | `3.5.43` | 3.5 | No fixed EOL | Installed by Nuxt |
| TypeScript | `6.0.3` | 6.0 (held back) | — | Don't upgrade to 7.x yet. [Why](#typescript-60) |
| `vue-tsc` | `3.3.11` | Latest | — | |
| `tailwindcss` | `4.3.3` | 4.3 | — | Must match `@tailwindcss/vite` |
| `@tailwindcss/vite` | `4.3.3` | 4.3 | — | Must match `tailwindcss` |
| `@tailwindcss/typography` | `0.5.20` | Latest | — | |
| `@nuxtjs/color-mode` | `4.0.1` | Latest | — | |

**Pinned in:** `frontend/package.json` (ranges) and `frontend/package-lock.json` (exact).

## Infrastructure and tooling

| Component | Version | Track | Supported until | Notes |
|---|---|---|---|---|
| Caddy | `2.11.4` | 2.x | No fixed EOL | |
| Docker Engine | 29.x | Latest | — | Dev machine and VM; not pinned |
| Docker Compose | 5.x | Latest | — | Dev machine and VM; not pinned |
| just | `1.58.0` | Latest | — | Homebrew locally, system package on the VM |

## Docker images

| Image | Used for | Pinned in |
|---|---|---|
| `python:3.14.7-slim-trixie` | Backend base image | `docker/Dockerfile.dev`, `docker/Dockerfile.prod` |
| `ghcr.io/astral-sh/uv:0.12.21` | Copies the `uv` binary into the backend images | `docker/Dockerfile.dev`, `docker/Dockerfile.prod` |
| `node:24.21.0-trixie-slim` | Frontend base image | `docker/Dockerfile.dev`, `docker/Dockerfile.prod` |
| `caddy:2.11.4-alpine` | Reverse proxy and automatic HTTPS | `docker-compose.prod.yaml` |

## Why these choices

### Python 3.14

Python has no LTS. 3.14 gets bug fixes until 2027-10-01, then security fixes only until 2030-10-31. Django 5.2.17 and Wagtail 7.4.3 both list Python 3.14 support. gunicorn's PyPI classifiers stop at 3.13, but gunicorn's own Docker images run on 3.14.

### Node.js 24

Node 24 is Active LTS until 2026-10-20, then Maintenance LTS until 2028-04-30. Nuxt 4.5 requires Node `^22.19 || ^24.11 || >=26`. Node 26 becomes LTS on 2026-10-28 and is supported until 2029-04-30. Switching later means changing the version in each place it's pinned.

### Debian-based images

Debian 13 gets regular security support until 2028-08-09, then Debian LTS until 2030-06-30. The backend and frontend images both use Debian, so the C library and locales match. Only Caddy uses Alpine.

### Wagtail 7.4 LTS

Wagtail 7.4 LTS gets fixes until 2027-11-02. The next LTS is expected around May 2027 (provisionally 8.3, per the [Wagtail release schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule)). Upgrade before 7.4 ends.

Wagtail 8.0 was not chosen because:

- It's supported only until 2027-02-02.
- Its new v3 API is a preview that may change in any release.
- `wagtail-headless-preview` 0.9.0 lists Wagtail 7 support only.

### SQLite

A blog is almost all reads with one author writing, and Nuxt caches pages, so most visits never reach the database. SQLite handles that comfortably, removes the database container, and a backup is a single file.

Settings it needs (Django 5.2 supports all of them):

- WAL journal mode, so readers aren't blocked while a write is happening.
- `IMMEDIATE` transactions and a busy timeout, so two writes at the same moment wait for each other instead of failing with "database is locked".

**Backups:** never copy the live database file. Run SQLite's backup command on a schedule, or use Litestream (`0.5.17`) to stream changes to object storage continuously.

**Switch to PostgreSQL if:**

- the backend needs to run on more than one server,
- a feature writes to the database on every visit (view counters, analytics), or
- you need better search ranking than Wagtail's SQLite search (FTS5) gives, or another PostgreSQL-only feature.

### TypeScript 6.0

TypeScript 7.0 (the new native compiler) is npm's default `latest`, but `vue-tsc`, which type-checks `.vue` files, doesn't work with it yet:

- [vuejs/language-tools#6124](https://github.com/vuejs/language-tools/issues/6124) and [#5381](https://github.com/vuejs/language-tools/issues/5381) track the incompatibility.
- The [TypeScript 7 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) also says Vue projects can't use it yet.

Stay on 6.0.x until `vue-tsc` supports 7. Progress is tracked in [vuejs/language-tools#6170](https://github.com/vuejs/language-tools/pull/6170).

## Review calendar

| When | What happens | Action |
|---|---|---|
| 2026-10-28 | Node 26 becomes LTS | Optional: move from Node 24 (supported until 2028-04-30) |
| 2027-04 | Django 6.2 LTS expected | Plan one combined upgrade with the next Wagtail LTS |
| 2027-05 | Next Wagtail LTS expected (provisionally 8.3) | Upgrade Wagtail and Django together |
| 2027-10-01 | Python 3.14 moves to security-only fixes | Consider moving to a newer Python |
| 2027-11-02 | Wagtail 7.4 LTS ends | Must be on the next Wagtail LTS by this date |
| 2028-04-30 | Django 5.2 LTS and Node 24 reach end of life | Must be upgraded by this date |
| 2028-08-09 | Debian 13 regular security support ends | Move images to the next Debian release |

## How to refresh this file

- **Support dates:** [endoflife.date](https://endoflife.date/) — check python, django, wagtail, nodejs, nuxt, ubuntu and debian.
- **Wagtail LTS plan:** [Wagtail release schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule).
- **Outdated packages:** run `uv tree --outdated` in `backend/` and `npm outdated` in `frontend/`.
