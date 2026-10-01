# Turn on the newsletter in production with a real email address

This guide takes the newsletter from "code is deployed" to "subscribers get your posts". It assumes the site already runs in production as described in the [`README`](../README.md) (Docker Compose on the Hetzner VM, Caddy in front). To try the newsletter on your own machine first, see [`local-development.md`](local-development.md).

Provider facts (limits, host names, ports) were checked against the providers' own documentation in **October 2026**. They change. If something doesn't match, trust the provider's page, and update this file.

## How it works

1. A visitor enters an address in the footer box. The site sends a confirmation email with a link (double opt-in). Nobody is subscribed until they click it.
2. After the click the address is **Subscribed**.
3. In the admin you open a live post and press **Email subscribers**. This only queues one delivery per subscribed address.
4. The **worker** (its own container, `worker`) sends the queue in the background, one email at a time, with a pause between emails, and retries failures later.
5. Every post email has an **Unsubscribe** link and the standard one-click unsubscribe header, so mail apps can show their own "Unsubscribe" button.

What is stored, all in the SQLite database: the address (lower-case), its status (waiting for confirmation, subscribed, unsubscribed), a random token used in the links, and the dates of signup, confirmation and unsubscribing. For each emailed post it stores one delivery per subscriber (queued, sent, failed, skipped). No tracking pixels, no click tracking.

Two services send email: the **backend** sends the confirmation emails (immediately, when someone signs up) and the **worker** sends the post emails. Both read the same `EMAIL_*` settings from `backend/.env`.

## 1. Choose how to send

Your server can't just send mail by itself: big providers reject mail from a random VM. You send through an SMTP account instead. Two options.

| | A. Gmail address | B. Your own domain through a sending service |
|---|---|---|
| Setup time | About 10 minutes | About an hour, plus waiting for DNS |
| Cost | Free | Free for a small list (Brevo) |
| From address | `you@gmail.com` | `newsletter@prabuddh.in` |
| DNS changes | None | Yes (a few TXT records) |
| Limit | About 500 emails a day | Brevo free: 300 a day (as of October 2026) |
| Best for | Trying it, or a few dozen subscribers | Anything you plan to keep |

If you aren't sure, start with A to check that everything works, and move to B when the list grows. Switching later only means changing a few lines in `backend/.env`.

### Option A: a Gmail address

Needs a personal Google account with **2-Step Verification** on. Google's own page says you must have it to create an app password, and app passwords aren't available for work or school accounts, accounts that only use security keys, or accounts with Advanced Protection ([Google: sign in with app passwords](https://support.google.com/accounts/answer/185833)).

1. Turn on 2-Step Verification for the account (Google Account → Security).
2. Open <https://myaccount.google.com/apppasswords>, create an app password named "prabuddh.in newsletter" and copy the 16 characters. Google shows it once. Treat it like a password.
3. Use the settings from [section 2](#2-put-the-settings-in-backendenv).

Limits and gotchas:

- Gmail lets a personal account send **500 emails a day**. When you go over, sending is blocked for 1 to 24 hours ([Google: Gmail sending limits](https://support.google.com/mail/answer/22839)). SMTP sends count toward it, and so do your normal emails from that account. With a list over a few hundred, use Option B.
- Keep `DEFAULT_FROM_EMAIL` equal to the Gmail address. Gmail replaces other From addresses with your own.
- Gmail signs the mail itself, so SPF and DKIM pass without any DNS work. The mail comes from your personal address, so keep replies in mind: they land in your normal inbox.

Gmail's SMTP server is `smtp.gmail.com` with port 587 (STARTTLS) or 465 (SSL) ([Google: SMTP settings](https://knowledge.workspace.google.com/admin/gmail/send-email-from-a-printer-scanner-or-app)). Use 587.

### Option B: your own domain through a sending service

Mail from `newsletter@prabuddh.in` looks more trustworthy, replies can go wherever you want, and a sending service has the reputation and the tools (bounce handling, logs) that Gmail doesn't. The worked example here is **Brevo**.

**Brevo (as of October 2026)**

- SMTP server `smtp-relay.brevo.com`, port **587** (STARTTLS). Brevo also offers 2525 and 465 (SSL) ([Brevo: SMTP relay](https://developers.brevo.com/docs/smtp-integration), [Brevo: send using SMTP](https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP)).
- Login: the **SMTP login** shown in your account (Settings → SMTP & API → SMTP). It is either your Brevo email address or something like `1234567@smtp-brevo.com`. It is **not** the relay host name.
- Password: an **SMTP key** you generate on the same page ([Brevo: SMTP keys](https://help.brevo.com/hc/en-us/articles/7959631848850-Create-and-manage-your-SMTP-keys)). Not your Brevo account password and not an API key.
- Free plan: 300 emails a day with no end date. Check the [pricing page](https://www.brevo.com/pricing/) for what it says now.

Steps:

1. Create a Brevo account. Brevo may ask you to verify the account before it lets you send.
2. Authenticate your domain: Settings → Senders, Domains & Dedicated IPs → Domains → add `prabuddh.in`. Brevo shows the DNS records to create. Add them at your DNS provider (see [DNS records](#dns-records-for-your-own-domain)). Brevo checks them and marks the domain authenticated ([Brevo: authenticate your domain](https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC)).
3. Add the From address as a sender: Senders tab → Add a sender (name "Prabuddh's Blog", email `newsletter@prabuddh.in`). With an authenticated domain it's verified automatically ([Brevo: create a sender](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email)).
4. Create an SMTP key and note the SMTP login.

**Other services** work the same way (an SMTP host, port 587, a login and a key): [Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html) (SMTP credentials are separate from your AWS keys, and you start in a sandbox until you ask AWS to lift it) and [Resend](https://resend.com/docs/send-with-smtp) (`smtp.resend.com`, user `resend`, an API key as the password, ports 25/465/587/2465/2587).

### Hetzner and the SMTP port

Hetzner blocks outgoing ports **25 and 465** on Cloud servers by default. **Port 587 is not blocked** ([Hetzner: Cloud server FAQ](https://docs.hetzner.com/cloud/servers/faq/)). Use port 587 with STARTTLS (`EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False`), as all examples here do. Don't use 465 on the VM, even if the provider offers it.

### DNS records for your own domain

Only for Option B. These records prove that mail from `prabuddh.in` is really yours. Without them, big providers send it to spam or reject it. The provider shows you the exact values; you add them at whoever hosts your DNS (the domain registrar, Cloudflare and so on).

- **SPF** (a TXT record on the domain): lists the servers allowed to send for the domain. Some providers need it (Amazon SES, for example); Brevo says it isn't required for domain authentication. If you already have an SPF record, never add a second one. Merge the provider's `include:` into the existing one.
- **DKIM** (a TXT or CNAME record): lets receivers check a digital signature on each email, which proves it wasn't changed. The provider gives you the name and value. For Brevo it's one TXT record (at `mail._domainkey`) or two CNAME records, depending on what its screen shows.
- **DMARC** (a TXT record at `_dmarc.prabuddh.in`): tells receivers what to do with mail that fails SPF/DKIM, and where to send reports. Start gentle:

  ```
  v=DMARC1; p=none; rua=mailto:you@prabuddh.in
  ```

  `p=none` only reports and rejects nothing, so it can't break your mail. Brevo suggests the same policy with its own report address. After a few weeks of clean reports, you can move to `p=quarantine`. Gmail and Yahoo expect a DMARC record from bulk senders.
- **Brevo code** (a TXT record, Brevo only): proves you own the domain.

DNS changes can take from minutes to a few hours. Check in Brevo that the domain shows as authenticated before you send.

## 2. Put the settings in `backend/.env`

On the server, open `backend/.env` (the file next to `backend/.env.example`; it is git-ignored and holds your secrets) and add the lines for your option. The Django security, host and URL settings are already in the file. Keep them.

Always set `FRONTEND_URL`. The links in emails (confirm, read the post, unsubscribe, the image) are built from it. If it's missing or points to `localhost`, every link in every email is broken.

**Option A, Gmail:**

```sh
FRONTEND_URL=https://prabuddh.in
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=Prabuddh's Blog <you@gmail.com>
NEWSLETTER_REPLY_TO=you@gmail.com
NEWSLETTER_SEND_DELAY=1.0
```

**Option B, Brevo with your domain:**

```sh
FRONTEND_URL=https://prabuddh.in
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-smtp-login-from-brevo
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
DEFAULT_FROM_EMAIL=Prabuddh's Blog <newsletter@prabuddh.in>
NEWSLETTER_REPLY_TO=you@prabuddh.in
NEWSLETTER_SEND_DELAY=1.0
```

What each line does:

| Variable | Meaning |
|---|---|
| `FRONTEND_URL` | Public address used in email links. `https://prabuddh.in` |
| `EMAIL_HOST`, `EMAIL_PORT` | The SMTP server. Use port 587 on Hetzner. |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | `True` / `False` for port 587. Never both `True`. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | The SMTP login and the app password or key. |
| `DEFAULT_FROM_EMAIL` | The From line: display name, then the address in `<>`. Must be an address your provider lets you send from. |
| `NEWSLETTER_REPLY_TO` | Optional. Where replies go. Leave it out and replies go to the From address. |
| `NEWSLETTER_SEND_DELAY` | Seconds between two post emails. Default 1. |
| `EMAIL_TIMEOUT` | Optional. Seconds to wait for the SMTP server. Default 20. |
| `NEWSLETTER_SUBSCRIBE_LIMIT` | Optional. Signup requests per visitor per hour. Default 10. |

Notes on the values:

- No spaces around `=`. Gmail shows app passwords in groups of four letters; remove the spaces.
- Docker Compose reads this file, and it treats `$` as the start of a variable and ` #` as the start of a comment, both without any warning. A password or key with a `$` or a `#` in it must go in single quotes, `EMAIL_HOST_PASSWORD='ab$cd#ef'`, or it gets cut short and the login fails. Single quotes keep everything exactly as written.
- The apostrophe in `DEFAULT_FROM_EMAIL=Prabuddh's Blog <you@gmail.com>` is fine without quotes. Double quotes work too: `DEFAULT_FROM_EMAIL="Prabuddh's Blog <you@gmail.com>"`.
- Leave `EMAIL_BACKEND` out. The production default is real SMTP.

## 3. Deploy

On the server, in the repository folder:

1. Pull the code and rebuild:

   ```sh
   git pull
   docker compose -f docker-compose.prod.yaml up -d --build
   ```

   This starts the new `worker` container too, and the backend applies the newsletter database migration when it starts.

2. After later edits to `backend/.env` only (no code change), recreate the two containers so they read the file again:

   ```sh
   docker compose -f docker-compose.prod.yaml up -d --force-recreate backend worker
   ```

3. Check that `backend`, `frontend`, `worker` and `caddy` are all running:

   ```sh
   docker compose -f docker-compose.prod.yaml ps
   ```

4. Check the worker. A healthy idle worker logs only its start line:

   ```sh
   docker compose -f docker-compose.prod.yaml logs --tail 20 worker
   ```

   Expect `Newsletter worker started.`

5. Run the production checklist. The email warning must be gone:

   ```sh
   docker compose -f docker-compose.prod.yaml exec backend python manage.py check --deploy
   ```

   If it says `newsletter.W001 Email isn't configured`, `EMAIL_HOST` or `DEFAULT_FROM_EMAIL` is still the default. (Two `security.W005`/`W021` warnings about HSTS also show up. They were already there.)

## 4. Test the email connection

Send a plain test email from inside the backend container. It uses the same settings as the newsletter. Use an address you can read.

```sh
docker compose -f docker-compose.prod.yaml exec backend python manage.py sendtestemail you@example.com
```

No output means success; check the inbox (and spam). If it fails, the last line of the error says why. See the [troubleshooting table](#troubleshooting).

## 5. Set up the site in the admin

1. Log in at <https://prabuddh.in/admin/>.
2. **Settings → Site Settings:** set **Site name**. The emails show it as the site name, and the confirmation email's subject uses it. It defaults to "My Site", which you don't want in an email.
3. **Settings → Footer Settings:** make sure **Show newsletter** is ticked, then Save. That's the switch for the signup box in the site footer (it's on by default).

## 6. Subscribe yourself

1. Open <https://prabuddh.in>, scroll to the footer, enter your own address and press Subscribe.
2. Wait for "Confirm your subscription to …" (a minute or two). Click the link. The page says "You're subscribed".
3. In the admin, **Newsletter → Subscribers** now lists you as "Subscribed".

If the form says "Something went wrong", look at the backend logs (`docker compose -f docker-compose.prod.yaml logs --tail 50 backend`) and the troubleshooting table.

## 7. Email your first post

1. Write the post and **Publish** it (only live posts can be emailed). After publishing, the admin shows a message "Email this post to N subscribers?" with an **Email subscribers** button. You can also use **More → Email subscribers** on the post.
2. On the post's newsletter page, look at the preview. It's the email exactly as sent.
3. Under **Send a test**, enter your address and press **Send a test**. Check how it looks in your mail app, on your phone too, and that the Read link and the Unsubscribe link open the right pages.
4. Press **Send to N subscribers**. This queues the emails, and the worker sends them in the background. The page shows how many are sent, queued and failed. Reload it to update.
5. A post can be emailed once. After sending, the same page shows the status and the last errors.

## 8. Check that it doesn't land in spam

1. In Gmail, open the received email, then the three-dot menu → **Show original**. At the top, **SPF**, **DKIM** and **DMARC** should all say **PASS**. With Option A they do automatically. With Option B, a FAIL means a DNS record is wrong or not published yet.
2. Optional: send a test to the address shown on <https://www.mail-tester.com> and read its score and notes. It's free with a daily limit.
3. Ask a friend with an Outlook or Yahoo address to subscribe and tell you where the mail lands.

## Day to day

- **Subscribers:** Newsletter → Subscribers. Filter by status, search by address. Export a CSV or XLSX with the export buttons.
- **Sent posts:** Newsletter → Sent posts lists every emailed post with sent, failed and waiting counts.
- **Failed deliveries:** open the post's newsletter page. It shows the last errors. Fix the cause (a wrong password, an exceeded quota), then press **Retry N failed**. The worker tries each delivery up to 5 times on its own, waiting 5, 10, 20 and 40 minutes between attempts. After 3 failures in a row it pauses the whole queue for 5 minutes, so an outage doesn't use up everyone's attempts.
- **Worker logs:** `docker compose -f docker-compose.prod.yaml logs -f worker`. Each batch logs a line like `Batch done: 50 sent, 0 failed attempts, 0 skipped.` A failed attempt is retried later, so it only becomes a failed delivery after the fifth one.
- **Sending speed and limits:** with the default 1 second pause, 300 emails take about 5 minutes. Raise `NEWSLETTER_SEND_DELAY` if your provider limits how fast you send. Stay under the daily limit of your provider (500 for Gmail, 300 for Brevo free). If the list is bigger than the limit, the rest fails and you'd retry the next day, so upgrade the plan or switch providers.
- **Backups:** the subscribers live in the SQLite database, in the `backend_data` volume. Never copy the live file. Make a safe copy with SQLite's backup function, then copy it off the server:

  ```sh
  docker compose -f docker-compose.prod.yaml exec backend python -c "import sqlite3; s=sqlite3.connect('/app/data/db.sqlite3'); d=sqlite3.connect('/app/data/backup.sqlite3'); s.backup(d); d.close(); s.close()"
  docker compose -f docker-compose.prod.yaml cp backend:/app/data/backup.sqlite3 ./backup-$(date +%F).sqlite3
  docker compose -f docker-compose.prod.yaml exec backend rm /app/data/backup.sqlite3
  ```

  Also see "Backups" in [`versions.md`](versions.md#sqlite).

## Privacy basics

- **Double opt-in.** Only an address whose owner clicked the confirmation link gets post emails. Someone else typing your address in the form only causes one confirmation email, and the same address isn't mailed again for 10 minutes.
- **Unsubscribing.** Clicking Unsubscribe (or the mail app's button) marks the address as unsubscribed. The row stays, so it is never mailed again. Signing up again with the same address sends a new confirmation.
- **Deleting someone.** If a person asks you to erase their data, open Newsletter → Subscribers, open the address and delete it. This also removes their delivery history.
- Say in your site's privacy text that you store email addresses to send new posts, and how people can unsubscribe.

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `SMTPAuthenticationError` (534, 535) in `sendtestemail` or logs | Wrong login or password. Gmail: use the 16-character app password, not your normal password, and check that 2-Step Verification is on. Brevo: use the **SMTP login** (not `smtp-relay.brevo.com`) and an **SMTP key** (not an API key or your account password). Remove stray spaces and quotes. |
| Timeout, `Connection refused` or `Network is unreachable` | Wrong port or a blocked one. Hetzner blocks 25 and 465. Use `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False`. |
| `SSL: WRONG_VERSION_NUMBER` | `EMAIL_USE_SSL=True` together with port 587. Switch to `EMAIL_USE_TLS=True` and `EMAIL_USE_SSL=False`. |
| `Sender address rejected` or the provider refuses the From | `DEFAULT_FROM_EMAIL` isn't an address you may send from. Gmail: use the Gmail address. Brevo/SES: add and verify the sender or domain. |
| Mail goes to spam | Own domain: check SPF, DKIM and DMARC (section 8), use a real From name, and send a few emails before a big one. Check mail-tester.com. Ask early subscribers to mark it "not spam". |
| "Daily user sending limit exceeded" or a 550 quota error | The provider's daily limit. Wait up to 24 hours and press **Retry N failed** on the post's newsletter page, or move to a bigger plan. |
| "Something went wrong" under the signup form | The confirmation email couldn't be sent. Run `sendtestemail`, then look at `docker compose -f docker-compose.prod.yaml logs backend`. |
| Queued emails never go out | The worker isn't running. `docker compose -f docker-compose.prod.yaml ps worker`, then `logs worker`. Restart it with `docker compose -f docker-compose.prod.yaml up -d worker`. |
| Worker logs `no such table` | The migration hasn't run. It runs when the backend starts: `docker compose -f docker-compose.prod.yaml up -d --build` and wait a minute. |
| Links in emails point to `localhost` or the wrong site | `FRONTEND_URL` is missing or wrong in `backend/.env`. Fix it and recreate `backend` and `worker` (step 2 of "Deploy"). |
| Images are missing in the email | `FRONTEND_URL` is wrong, or `/media/` isn't reachable from the internet. Open `https://prabuddh.in/media/` URLs of an uploaded image in a browser. |
| The email says "My Site" | Set **Site name** in Settings → Site Settings. |
| `newsletter.W001` in `check --deploy` | `EMAIL_HOST` is still `localhost` or `DEFAULT_FROM_EMAIL` is `webmaster@localhost`. |
| Edited `backend/.env` but nothing changed | The containers read it at start. Recreate them (step 2 of "Deploy"). |
