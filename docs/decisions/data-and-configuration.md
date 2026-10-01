# Data and configuration

The database, settings, secrets and versions. See the [index](README.md) for the other areas.

---

## D1. SQLite as the database

**Decision.** The site uses SQLite: one database file on the server. It is tuned for a web server in `backend/config/settings/base.py`:

- **WAL journal mode:** people can read while a write is in progress.
- **`IMMEDIATE` transactions with a 20-second busy timeout:** two writes at the same moment queue up instead of one failing with "database is locked".
- **`synchronous=NORMAL`, plus memory-mapping and cache settings:** fast and safe with WAL. A power cut can lose the last transaction, but it can't corrupt the file.

**Why.** You asked whether SQLite is enough for a simple or medium blog. It is:

- A blog is almost all reads, from one author writing, and SQLite serves thousands of reads a second from a local file.
- It removes a whole database service: no container, no password, no version upgrades, no separate backups.
- It's one file to back up and move.
- The newsletter queue lives in the same file. The web server and the worker writing at the same moment is exactly what the `IMMEDIATE` and timeout settings handle.

**Why not the alternative.** PostgreSQL is excellent, but here it would add a container to run, tune, upgrade and back up, with no benefit at this size.

**When to revisit.** Switch to PostgreSQL if:

- the backend has to run on more than one server,
- a feature writes on every page view (view counters, likes, comments with heavy traffic), or
- search quality needs PostgreSQL's full-text search.

The same list is in [`versions.md`](../versions.md#sqlite).

---

## D2. The database lives in a Docker volume, never in a shared folder

**Decision.** In Docker, the database sits in a named volume (`backend_data`), in development too, even though the code itself is mounted from your disk.

**Why.** WAL mode coordinates readers and writers through a small shared-memory file. Folders shared from macOS into Docker's Linux VM don't reliably support that, which risks a corrupted database. A named volume lives inside the VM's own filesystem, where it works properly.

---

## D3. Backups use SQLite's backup command

**Decision.** Backups use SQLite's backup function (a one-line Python command in [`newsletter-production.md`](../newsletter-production.md#day-to-day)). Never copy the live file.

**Why.** With WAL, recent changes may sit in a separate `-wal` file, so copying the main file while the site runs can capture a broken or incomplete database. The backup function takes a consistent snapshot while the site keeps running.

**Not set up yet.** Nothing runs backups on a schedule. The simplest next step is a daily cron job on the server that runs the backup command and copies the file off the machine. [Litestream](https://litestream.io) is the step up: it streams every change to object storage continuously. This matters more now that the database holds subscribers.

---

## D4. Settings split by environment and read from the environment

**Decision.** Django settings are split into `base.py` (shared), `dev.py` and `production.py`. Values that differ between machines come from environment variables, read with django-environ (your choice).

- **Development** works with no setup at all: debug on, a throwaway secret key, emails printed to the terminal.
- **Production** refuses to start without `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `WAGTAILADMIN_BASE_URL` and `FRONTEND_URL`. It turns on secure cookies, HSTS and trust in Caddy's HTTPS header.

**Why.**

- Starting locally needs no configuration.
- Production fails loudly at start instead of quietly running with `localhost` defaults or a missing secret.
- Secrets live only in the environment, never in git.
- django-environ reads `.env` files and converts types (true/false, numbers, comma-separated lists) in one small, stable library.

**Why not the alternative.** One settings file full of `if DEBUG:` branches makes it easy for a development default to leak into production.

---

## D5. One env file per program

**Decision.** There are three `.env` files. Each has a committed `.env.example`, and the real ones are git-ignored and kept out of Docker images by `.dockerignore`.

| File | Read by | Holds |
|---|---|---|
| `.env` (root) | Docker Compose, only to fill in `${DOMAIN}` | `DOMAIN` |
| `backend/.env` | Django: through Compose's `env_file` in Docker, or django-environ directly when run without Docker | Secrets, URLs, email settings |
| `frontend/.env` | Nuxt, when run without Docker | Optional overrides of the backend and site address |

**Why.**

- Each program reads the file in its own folder automatically, so nothing needs extra flags.
- Secrets reach only the containers that use them. The backend and worker get `backend/.env`; the Nuxt and Caddy containers never see the Django secret key or the SMTP password.

**Why merging them was rejected.** You asked about putting the root and backend files together. It doesn't give you one file for everything, because Nuxt run without Docker still reads `frontend/.env`. It would also mean changing where Django looks, and it puts all secrets one careless `env_file` line away from containers that shouldn't have them.

**Known wart, with a fix not yet applied.** The domain is typed five times: `DOMAIN`, plus `FRONTEND_URL`, `WAGTAILADMIN_BASE_URL`, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `backend/.env`. The recommended fix is to have `docker-compose.prod.yaml` build those four from `${DOMAIN}`. `backend/.env` would then hold only secrets, and a typo in one copy could no longer break admin logins or email links. It's about 10 lines, and existing servers keep working because Compose's `environment:` overrides `env_file:`.

---

## D6. Email settings as separate variables

**Decision.** Email is configured with separate variables (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`…) rather than one `EMAIL_URL`.

**Why.** In a URL, a password containing `/`, `@` or `:` must be percent-encoded, and getting that wrong only shows up as a login failure. Separate variables are readable and need no encoding.

A related trap, now documented: Docker Compose treats `$` in `backend/.env` as the start of a variable and ` #` as a comment, without warning. A password containing either must be wrapped in single quotes.

---

## D7. Long-supported versions, pinned twice

**Decision.**

- **Releases.** Use the long-term-support release wherever a project has one: Django 5.2, Wagtail 7.4, Node 24, Ubuntu 26.04.
- **Pinning.** `pyproject.toml` and `package.json` pin the release line, the lock files (`uv.lock`, `package-lock.json`) pin exact versions, and Docker images use exact tags.
- **Tracking.** Every version, its support end date and the reason for it are kept in [`versions.md`](../versions.md), with a review calendar.

**Why.** Upgrades happen on a schedule you choose instead of as surprises. Every install, locally and on the server, gets exactly the same versions. After months away, one file tells you what is due.

**Notable holds** (details in `versions.md`):

- **TypeScript stays on 6.0,** because `vue-tsc`, which type-checks `.vue` files, doesn't support TypeScript 7 yet.
- **Wagtail stays on 7.4 LTS rather than 8.0,** because 8.0's support ends sooner, its new API is a preview, and the preview package supports only Wagtail 7.

**Not set up yet.** Nothing proposes updates automatically. Dependabot or Renovate could open pull requests for new versions; for now the review calendar is the reminder.

---

## D8. uv for Python, npm for Node

**Decision.** The backend uses uv; the frontend uses npm.

**Why.**

- **uv** installs fast, writes an exact lock file, and installs the right Python version itself (from `.python-version`). The same uv binary is copied into the Docker images from its official image, so local and Docker installs behave the same.
- **npm** comes with Node, so there's no extra tool to install (pnpm or Yarn would be one more), and its lock file pins every package.
