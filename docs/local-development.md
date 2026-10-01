# Run the project locally

How to start the blog on your own machine, set it up in the admin, and try the newsletter without sending a real email. For production, see [`newsletter-production.md`](newsletter-production.md).

Two ways to run it. Pick one.

- **Option A, Docker:** one command starts everything (backend, frontend, the newsletter worker and a test inbox). Easiest.
- **Option B, without Docker:** you run each part yourself in its own terminal. Closer to the code, and faster to restart.

Don't run both at the same time. They use the same ports (3000, 8000, and 8025 for the inbox) and have separate databases.

## What to install

| For | Install | Version |
|---|---|---|
| Option A | [Docker](https://docs.docker.com/get-docker/) with Compose | Docker Engine 29.x, Compose 5.x |
| Option A, optional | [just](https://just.systems), for short commands | 1.58 |
| Option B | [just](https://just.systems) | 1.58 |
| Option B | [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 for you) | 0.12 |
| Option B | [Node.js](https://nodejs.org) | 24 LTS (`>=24.11 <25`) |
| Option B | Docker, only for the test inbox (Mailpit) | as above |

Exact versions and why they were chosen: [`versions.md`](versions.md).

## Option A: Docker

Run everything from the repository root.

1. Start the stack. The first build takes a few minutes.

   ```sh
   just docker-dev
   ```

   Without `just`: `docker compose -f docker-compose.dev.yaml up --build`

2. In a second terminal, create your admin login (once per database).

   ```sh
   just docker-manage createsuperuser
   ```

3. Open the pages.

   | What | URL |
   |---|---|
   | The site | <http://localhost:3000> |
   | Wagtail admin | <http://localhost:8000/admin/> |
   | Test inbox (Mailpit) | <http://localhost:8025> |

The stack has four containers: `backend` (Django, runs the migrations on start), `frontend` (Nuxt), `worker` (sends the newsletter queue) and `mailpit` (catches every email).

**Live reload.** `./backend` and `./frontend` are mounted into the containers, so saved edits show up without a restart. The worker also restarts itself when backend code changes.

**Stop it.** Press `Ctrl+C` in the first terminal, or run `just docker-dev-down` (the database is kept).

**Where the data lives.** The database is in the Docker volume `backend_data` (`prabuddh-me-dev_backend_data`), not in `backend/data/`. Uploaded images go to `backend/media/` on your disk. Emails caught by Mailpit are kept in memory and vanish when it restarts.

**Reset the database.** This deletes every post, setting and subscriber in the Docker database. Don't do it by accident.

```sh
docker compose -f docker-compose.dev.yaml down -v
```

The next `just docker-dev` starts from a fresh database, and you need to run `createsuperuser` again.

**After changing frontend dependencies** (`package.json`), add `-V` so the container rebuilds its `node_modules`:

```sh
docker compose -f docker-compose.dev.yaml up --build -V
```

## Option B: without Docker

You need three terminals: backend, frontend and worker. A fourth is only needed for the inbox.

1. Set up the backend once, from the repository root.

   ```sh
   just sync
   just migrate
   just createsuperuser
   ```

   This creates `backend/data/db.sqlite3`.

2. Terminal 1: backend on <http://localhost:8000>.

   ```sh
   just run
   ```

3. Terminal 2: frontend on <http://localhost:3000>.

   ```sh
   just install    # first time, and after package.json changes
   just dev
   ```

4. Terminal 3: the newsletter worker. Skip it if you aren't trying the newsletter.

   ```sh
   just worker
   ```

5. Email. By default the backend prints emails in the terminal where it runs (the confirmation email in terminal 1, post emails in terminal 3). That is enough to copy a link. To see emails in a real inbox, use Mailpit:

   ```sh
   just mailpit    # terminal 4: SMTP on :1025, inbox on http://localhost:8025
   ```

   Create `backend/.env` (it is git-ignored) with these lines, then restart the backend and the worker:

   ```sh
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=localhost
   EMAIL_PORT=1025
   EMAIL_USE_TLS=False
   ```

   `just mailpit` starts only the `mailpit` container from the dev compose file, so it can't run together with Option A.

Stop each server with `Ctrl+C`. The database stays in `backend/data/`. To reset it, stop the servers, delete `backend/data/db.sqlite3*` and run `just migrate` and `just createsuperuser` again.

## First steps in the admin

A fresh database already has a page called "Home" (created by the migrations in `backend/home/migrations/`) and nothing else. Log in at <http://localhost:8000/admin/>.

1. **Settings → Site Settings:** set **Site name** to your blog's name. It defaults to "My Site", and the newsletter emails use it.
2. **Settings → Header Settings, Footer Settings, Author Settings:** set the menu, footer text and your details. Footer Settings has the **Show newsletter** switch for the signup box (on by default).
3. **Pages → Home → Add child page → Blog Post:** add a post. Give it a title, a date and an intro, add some body text, then **Publish**. Posts can only be added under Home.
4. Reload <http://localhost:3000>. The post shows on the home page and at `/blog/`.

## Try the newsletter locally

This works with both options. The steps assume the inbox at <http://localhost:8025> (Docker, or Option B with Mailpit). Without Mailpit, read the links in the terminal output instead.

1. **Subscribe.** Scroll to the footer of <http://localhost:3000>, enter an address (any, e.g. `reader@example.com`) in "Stay Updated" and press Subscribe. The form says to check your inbox.
2. **Read the confirmation email** in the inbox: "Confirm your subscription to …".
3. **Confirm.** Click the link in the email (it points to `/newsletter/confirm/?token=…`). The page says "You're subscribed".
4. **Check the list.** In the admin, open **Newsletter → Subscribers**. The address has the status "Subscribed".
5. **Email a post.** Open the post under **Pages**, then use the **More** menu (top right) → **Email subscribers**. After publishing a post, a message with an **Email subscribers** button also appears.
6. **Send a test first.** On the page, check the preview, enter an address under **Send a test** and press **Send a test**. The mail arrives in the inbox with "[Test]" in the subject.
7. **Send for real.** Press **Send to N subscribers**. This only queues the emails. The worker sends them within about ten seconds. The page then shows how many were sent. If nothing arrives, see Troubleshooting.
8. **Unsubscribe.** Open the email in the inbox and click **Unsubscribe**, then press the **Unsubscribe** button on the page. The status in **Newsletter → Subscribers** changes to "Unsubscribed".

A post can be emailed only once. To try again, write another post.

Watch the worker with `docker compose -f docker-compose.dev.yaml logs -f worker` (Docker) or in its terminal (Option B). It prints a line like `Batch done: 1 sent, 0 failed attempts, 0 skipped.` when it sends.

## Checks before committing

Run these from the repository root. Docker doesn't need to be stopped for the backend checks.

```sh
just test                 # backend tests (core, blog and newsletter)
just lint                 # ruff format and check
just makemigrations-check # fails if a model change has no migration
```

Stop the Docker stack before the frontend checks, because the dev container writes `frontend/.nuxt` and the two would collide:

```sh
just docker-dev-down
just typecheck
just build
just docker-dev           # start it again
```

## Troubleshooting

| Problem | Fix |
|---|---|
| "port is already allocated" or "address already in use" | Something else uses 3000, 8000, 8025 or 1025. Stop the other stack (Option A and Option B can't run together), or find the process with `lsof -i :8000`. |
| An edit doesn't show up | Docker: check that the `frontend` and `backend` containers are running (`docker compose -f docker-compose.dev.yaml ps`). Frontend changes in a new file can need a page reload. Backend settings changes need a restart: `docker compose -f docker-compose.dev.yaml restart backend worker`. |
| The frontend fails after changing `package.json` | Rebuild with `docker compose -f docker-compose.dev.yaml up --build -V`. Without Docker: `just install`. |
| "no such table" | The database has no tables yet. Docker: `docker compose -f docker-compose.dev.yaml restart backend` (it migrates on start). Without Docker: `just migrate`. |
| The signup form says "Something went wrong" | The backend isn't running or can't send email. Check the backend logs for the error. |
| Emails don't arrive in Mailpit | Confirmation emails are sent by the backend, post emails by the worker. Check `docker compose -f docker-compose.dev.yaml logs worker mailpit`. Without Docker, check that `just mailpit` and `just worker` are running and that `backend/.env` has the Mailpit lines. |
| Queued emails never go out | The worker isn't running. Docker: `docker compose -f docker-compose.dev.yaml ps worker`. Without Docker: `just worker`. |
| The signup box is missing | **Settings → Footer Settings → Show newsletter** is off. |
| Links in emails go to the wrong address | `FRONTEND_URL` isn't `http://localhost:3000`. Remove it from `backend/.env` or fix it. |
