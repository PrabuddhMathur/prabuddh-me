# Infrastructure

Docker, the server, HTTPS and the tools you run day to day. See the [index](README.md) for the other areas.

---

## E1. One server running Docker Compose

**Decision.** Production is one Hetzner VM (Ubuntu 26.04 LTS) running `docker-compose.prod.yaml`, which starts four containers: Caddy, the Wagtail backend, the newsletter worker and the Nuxt frontend. The database and uploads live in Docker volumes on the same disk.

**Why.**

- A personal blog fits comfortably on one small VM.
- Compose starts, restarts (`restart: unless-stopped`) and connects four containers with a single file and command, with nothing new to learn.
- Hetzner is inexpensive and has EU locations.
- With everything on one disk, a backup is the database file plus the media folder.

**Why not the alternatives.**

- **Kubernetes or Docker Swarm.** Built for fleets of servers. Here they would add complexity and nothing else.
- **Platforms such as Render, Fly.io or Railway.** You pay per service, and SQLite on their disks is awkward, because some platforms wipe the disk on every deploy.
- **Serverless hosting.** Wagtail's admin and a SQLite file don't fit the model.

**When to revisit.** If one server is ever not enough, the move comes as a package: PostgreSQL ([D1](data-and-configuration.md#d1-sqlite-as-the-database)), object storage for media ([A5](architecture.md#a5-caddy-serves-uploads-whitenoise-serves-the-admins-files)) and a load balancer.

---

## E2. All Docker files together at the root

**Decision.** This layout was your choice:

- `docker/Dockerfile.dev` and `docker/Dockerfile.prod`, each with a `backend` and a `frontend` target.
- `docker-compose.dev.yaml` and `docker-compose.prod.yaml` at the root.
- The repository root as the build context.

A `.dockerignore` lets only `backend/` and `frontend/` into builds, minus local files: `.env`, virtualenvs, `node_modules`, the database and media.

**Why.**

- All container configuration is in one place.
- One Dockerfile per environment keeps the two apps' setups side by side, which makes it easy to keep base image versions in step (they must match `versions.md`).
- Targets let Compose build both apps from the same file.
- The whitelist-style `.dockerignore` means secrets and local databases can't end up inside an image, even by accident.

---

## E3. Lean, locked-down production images

**Decision.**

- **Backend.** A two-stage build:
  - The build stage installs exactly the locked packages, without development tools (`uv sync --locked --no-dev`), and collects the admin's static files using throwaway settings.
  - The runtime stage contains Python, the installed packages and the code, and nothing else.
  - It runs as an unprivileged user (`app`). The code is owned by root, so that user can't change it; only `data/` and `media/` are writable.
  - gunicorn serves requests with 2 worker processes of 4 threads each.
- **Frontend.** The build stage runs `npm ci` and `nuxt build`. The runtime stage contains only Nuxt's self-contained `.output` folder and runs as the unprivileged `node` user.

**Why.**

- Builds are reproducible: the same lock file gives the same image.
- The runtime images carry no compilers, package managers or dev tools, which means less to attack and less to download.
- If someone ever found a hole in the app, they couldn't rewrite its code.
- Threaded workers suit a small VM where most time is spent waiting on the database or the network.

---

## E4. A development stack with live reload

**Decision.** `docker-compose.dev.yaml` mounts `backend/` and `frontend/` from your disk into the containers, and runs Django's dev server, the Nuxt dev server, the newsletter worker (restarting on code changes) and Mailpit. Details:

- **File watching.** The frontend watches files by polling (`CHOKIDAR_USEPOLLING`).
- **`node_modules`.** It stays inside the container in a volume of its own.
- **The database.** It sits in a named volume ([D2](data-and-configuration.md#d2-the-database-lives-in-a-docker-volume-never-in-a-shared-folder)).

**Why.**

- You edit on your Mac and see the change straight away, while everything runs on the same Linux and versions as production.
- Polling is needed because folders shared from macOS (through Colima) don't send "file changed" events into the container. Without it, new or edited files were missed until a restart.
- `node_modules` stays in the container because it contains Linux binaries that must not mix with your Mac's.

---

## E5. Caddy in front

**Decision.** Caddy is the only container exposed to the internet (ports 80 and 443, including HTTP/3).

- **HTTPS:** it gets and renews certificates automatically.
- **Routing and files:** it routes by path ([A2](architecture.md#a2-one-domain-split-by-path)) and serves `/media/`.
- **Compression and redirects:** it compresses responses and redirects `www.` to the bare domain.
- **Headers:** it tells the backend the visitor's real IP address (`X-Real-IP`, used by the newsletter's rate limit) and the original scheme.

The `caddy_data` volume keeps the certificates.

**Why.** Automatic HTTPS with about 30 lines of readable configuration is hard to beat. Keeping the certificates in a volume avoids asking Let's Encrypt for new ones on every restart, which could hit their rate limits.

**Why not the alternatives.**

- **nginx with certbot.** Two tools, a renewal timer to keep alive, and a longer configuration.
- **Traefik.** Its routing lives in container labels, which is less direct than one file for a fixed set of routes.

---

## E6. HTTPS is handled by Caddy alone

**Decision.**

- Caddy redirects HTTP to HTTPS. Django's own redirect is off, and the matching Django warning is silenced.
- Django trusts Caddy's header saying the original request was HTTPS, so it builds secure links and marks cookies secure.
- HSTS (telling browsers "only ever use HTTPS here") starts at one hour (`SECURE_HSTS_SECONDS=3600`).

**Why.**

- Django's redirect would also redirect the Nuxt server's internal `http://backend:8000` calls ([A3](architecture.md#a3-the-nuxt-server-calls-wagtail-directly-inside-docker)).
- The short HSTS is deliberate. A long HSTS combined with a certificate problem would lock visitors out until it expires. Once HTTPS has worked for a while, raise it to a year (`31536000`).

---

## E7. Migrations run when the backend starts

**Decision.** The production backend container runs `manage.py migrate` before it starts gunicorn. The worker container never does.

**Why.** Deploying is one command (`docker compose … up -d --build`) with no step to forget. Only one container migrates, so two processes can never change the database schema at the same time. The worker doesn't migrate; if it starts before the migration finishes, it logs the error, waits a few seconds and tries again.

**When to revisit.** If you ever run more than one backend container, move migrations into a one-off job.

---

## E8. `just` as the task runner

**Decision.** This was your choice: common commands are recipes in the root `justfile`, covering backend, frontend and Docker. There is no Makefile.

**Why.**

- `just` on its own lists every recipe with its comment.
- Recipes can set their own working directory, so you run everything from the root.
- Extra arguments pass straight through, as in `just docker-manage createsuperuser`.
- There are none of Make's traps (tabs versus spaces, `.PHONY`, file-timestamp logic).

Each recipe is a thin wrapper, so the underlying command is always visible in the `justfile` if you need to run it by hand.
