# Newsletter

Why the newsletter works the way it does. For running it, see [`local-development.md`](../local-development.md#try-the-newsletter-locally) and [`newsletter-production.md`](../newsletter-production.md). See the [index](README.md) for the other areas.

The guiding idea: a personal blog's newsletter is "email me when there's a new post". It should never mail someone who didn't ask, never lose or double-send an email, survive a bad password or a full quota without harm, and add no new services to run.

---

## N1. Double opt-in

**Decision.** A signup only creates a "waiting for confirmation" entry and sends one email with a link. Nobody gets posts until they click it.

**Why.**

- Anyone can type anyone's address into a form. Double opt-in means only the owner of an address can subscribe it.
- Mail providers judge a sender by complaints and bounces. Mailing only confirmed addresses keeps those near zero, which keeps your mail out of spam.
- It gives you a record of consent (the confirmation time), which privacy laws such as GDPR expect.

**Why not the alternative.** Single opt-in, where any entered address gets posts, invites typos, fake addresses and people subscribing others. Each of those turns into bounces or "this is spam" clicks against your sending reputation.

---

## N2. One random token per subscriber, stored in the database

**Decision.** Each subscriber gets one random 43-character token when the entry is created. It goes in the confirmation link and in every unsubscribe link, and it never changes.

**Why.** The link proves the visitor received an email at that address, without needing an account or a password. A stored token keeps working even if Django's `SECRET_KEY` is rotated, can be looked up directly, and is short enough for a link.

**Why not the alternative.** Tokens signed with `SECRET_KEY` (Django's signing module) need no column, but every link ever sent would break the day the key changes. Unsubscribe links in old emails must keep working.

---

## N3. A signup never reveals who is subscribed

**Decision.** Every valid signup shows the same "check your inbox" message: a new address, an existing subscriber, or someone waiting for confirmation. An existing subscriber gets no email.

**Why.** Otherwise the form would let anyone test whether a given address is on your list.

---

## N4. Spam protection without a CAPTCHA

**Decision.** Three light defences:

- **A honeypot field.** A hidden input that people never see but bots fill in. A filled one is quietly ignored.
- **A per-visitor limit.** At most 10 signup attempts per IP address per hour (`NEWSLETTER_SUBSCRIBE_LIMIT`). The IP comes from Caddy's `X-Real-IP` header.
- **A per-address cooldown.** At most one confirmation email per address every 10 minutes.

**Why.** The real risk is someone using your form to send many confirmation emails, either to one victim or to many addresses, which could get your mail account suspended. These three stop that. Real visitors never see them, and they need no outside service.

**Why not the alternative.** A CAPTCHA (reCAPTCHA, hCaptcha, Turnstile) adds a third-party script that tracks visitors, slows the page, and annoys real people, which is too much for a footer form.

**Cost.** The count is kept per server process, and production runs two, so one visitor could get up to 20 attempts an hour. That's still far too few to abuse, and it avoids adding Redis just to share a counter.

---

## N5. Confirmation emails go out immediately, post emails through a queue

**Decision.** The confirmation email is sent while the signup request is being handled. Post emails are only queued by the admin and sent by a separate worker.

**Why.** A confirmation is one email, and the visitor is waiting for it. Sending it straight away gives instant feedback, and an honest "something went wrong" if the mail server refuses. A post goes to every subscriber, which can take minutes and can hit a provider's limits. That must never happen inside a web request, where a timeout would cut it off halfway.

---

## N6. A database queue and a small worker process

**Decision.** Pressing "Send to N subscribers" creates one `Delivery` row per subscriber in the existing SQLite database. The `newsletter_worker` command runs in its own container, built from the same image as the backend. It picks due rows and sends them one by one, then checks again every 10 seconds.

**Why.**

- **No new infrastructure.** It uses the database you already have and the image you already build.
- **It survives restarts.** The queue is on disk, so a deploy or a crash loses nothing; the worker carries on where it stopped.
- **It can go slowly.** Providers cap how much you can send per day, and some per minute. A worker can pace itself and wait out failures, which a web request can't.
- **It's visible.** Every delivery's state (queued, sent, failed, skipped) is a row you can see in the admin.

**Why not the alternatives.**

- **Celery or RQ with Redis.** The standard heavy setup: a broker service plus a worker, each with its own configuration and failure modes. Built for thousands of jobs a second; a blog sends a few hundred emails a month.
- **Sending inside the web request.** Hundreds of emails at about a second each would hit the 30-second request timeout and leave the send half-done.
- **A background thread inside the web server.** It dies silently when the server restarts, with no record of what was sent.
- **A cron job on the server.** It works, but it's set up outside the repository and is easy to forget on a new server. A Compose service is part of the deployment.
- **A newsletter service (Buttondown, Mailchimp, Substack).** Monthly cost, subscribers stored with a third party, their branding in your emails, and the signup sent through their forms. Worth it for a big audience, not for this.

**Cost.** One more container. It's the same image as the backend, so there's nothing new to build or update.

---

## N7. Sending safely: no doubles, retries, pauses, one connection

**Decision.** The worker:

- **Claims each row before sending it.** It changes the row from queued to sending in one database statement, so a second worker, or a manual run at the same time, can't send the same email twice.
- **Retries failures.** It tries each email up to 5 times, waiting 5, 10, 20 and then 40 minutes in between. After that the row is marked failed, and **Retry N failed** in the admin puts it back in the queue.
- **Stops early when the server is the problem.** After 3 failures in a row it stops the batch and pauses the whole queue for 5 minutes.
- **Reuses one mail-server connection per batch,** and opens a fresh one after an error.
- **Waits between emails** (`NEWSLETTER_SEND_DELAY`, 1 second by default).
- **Recovers from crashes.** Rows left "sending" for 15 minutes are put back in the queue.

**Why.**

- The claim makes double-sending impossible, even by accident.
- Retries ride out short outages, and the growing wait doesn't hammer a struggling server.
- The stop-and-pause rule is there because three failures in a row usually mean the problem is the server (a wrong password, a used-up quota, a network outage), not the recipients. Without it, one bad password would use up every subscriber's attempts within minutes.
- Logging in once per batch instead of once per email is faster, and providers rate-limit repeated logins.
- The delay keeps you under per-minute limits.

**The one gap.** If the worker crashes in the instant after an email was sent but before its row was marked sent, that one email goes out again after 15 minutes. A duplicate in that rare case is better than ever losing an email.

---

## N8. Each post is emailed once, on purpose, from the admin

**Decision.** A live post gets **More → Email subscribers**. That page shows a preview of the email and the number of recipients, lets you send yourself a test, and then sends to everyone. The database allows one send per post. After you publish a post that hasn't been emailed, the admin offers the same button in its confirmation message.

**Why.**

- Emailing is the one action you can't undo. In Wagtail, every later edit to a live post is published again, so sending automatically on publish risks mailing everyone about a typo fix, or mailing a post you published by mistake.
- An explicit button with a test email first is safe.
- The prompt after publishing keeps it nearly as convenient as automatic sending.
- The database rule makes a double send impossible, even with two clicks or two editors.

**Why not the alternatives.**

- **Automatic sending on first publish.** Convenient, but there's no chance to check the email first, and there are edge cases with unpublishing and republishing.
- **Free-form campaigns** (write any email to subscribers). More screens to build and maintain. The footer promises "new posts delivered to your inbox", and that's what this does. This is the natural extension point if you ever want announcements or digests.

---

## N9. The email is a teaser, not the whole post

**Decision.** A post email contains:

- the site name,
- the post title, date and reading time,
- the featured image,
- the intro,
- a **Read the post** button,
- an unsubscribe link.

**Why.** Posts are built from blocks (galleries, spoilers, call-to-actions, hero sections) that email apps can't display faithfully. Spoilers can't even hide in email. A short, clean email renders the same everywhere and brings readers to the site, where the post looks the way you designed it.

**Why not the alternative.** Full posts in email mean a second renderer for every block type, kept in step with the site forever, and still looking broken in some email apps.

---

## N10. Email HTML built for email apps

**Decision.** The emails use a single column at most 600 px wide, laid out with tables and inline styles only: no web fonts, no external CSS. A plain-text version always comes along, and the button uses the site's primary colour.

**Why.** Email apps, Outlook especially, still render HTML like it's 2005. They ignore `<style>` blocks, flexbox and web fonts. Tables with inline styles are what renders reliably in Gmail, Outlook and Apple Mail. The plain-text part is for text-only readers and spam filters, which distrust HTML-only mail.

---

## N11. Unsubscribing: a button on a page, plus one-click headers

**Decision.**

- The visible unsubscribe link opens a page with an **Unsubscribe** button. Merely opening the link never unsubscribes anyone.
- Every post email also carries the `List-Unsubscribe` and `List-Unsubscribe-Post` headers (RFC 8058). With these, Gmail, Yahoo and Apple Mail show their own unsubscribe button, which unsubscribes in one click.
- Unsubscribed addresses stay in the database, marked unsubscribed.

**Why.**

- Company mail filters and security scanners open every link in an email to check it. If opening the link unsubscribed people, they would be silently removed.
- The one-click headers are what Gmail and Yahoo require from bulk senders. They also give unhappy readers an easier option than the spam button, which protects your reputation.
- Keeping the row means a re-imported list or an old signup can never mail someone who left. Signing up again sends a fresh confirmation.

---

## N12. Confirming happens when the link opens

**Decision.** Opening the confirmation link confirms the subscription straight away, while the page is rendered.

**Why.** It's what people expect, and how most newsletters work: click, done. Adding a second "Confirm" button loses a real share of people who click, read the page and leave.

**Trade-off, accepted on purpose.** A mail scanner that opens links can confirm a subscription by itself. That's harmless: the address still received the email, and every later email can be unsubscribed from. Unsubscribing, by contrast, always needs the button ([N11](#n11-unsubscribing-a-button-on-a-page-plus-one-click-headers)).

---

## N13. It works without JavaScript

**Decision.** The signup form and the unsubscribe button are real HTML forms that post to the backend. With JavaScript (the normal case), the page sends them in the background and shows the result in place. Without it, the backend answers with a redirect to a page that shows the result: `/newsletter/?status=…` or `/newsletter/unsubscribe/?status=…`.

**Why.** Some readers use browsers or settings that block JavaScript. Supporting them costs a few lines, because the same endpoints serve both. The development proxy was adjusted to pass these redirects to the browser, the way Caddy does in production, so local testing behaves like the real site.

---

## N14. Deliverability details

**Decision.** Every email has:

- a `Message-ID` on your own domain,
- the unsubscribe headers,
- an optional `Reply-To` (`NEWSLETTER_REPLY_TO`),
- the From name and address you set in `DEFAULT_FROM_EMAIL`.

There are no tracking pixels and no rewritten links.

**Why.**

- Spam filters count small things. A message ID that names a Docker container, which Django would use by default, is one of them.
- No tracking keeps readers' privacy and leaves nothing to explain in a privacy note. Open rates aren't reliable anyway, because Apple Mail preloads every image.

---

## N15. Mailpit for local testing

**Decision.** The dev stack runs Mailpit, a fake mail server with a web inbox at <http://localhost:8025> that catches every email the site sends.

**Why.**

- You can see the real emails, with HTML, headers and links, and click through the whole flow locally.
- No email can ever reach a real person from your laptop.
- It's a single small container that needs no account.

**Why not the alternatives.** Printing emails to the terminal (still the default without Docker) hides the HTML. A real mail account risks mailing real addresses and needs credentials on every developer machine.

---

## N16. Recommended ways to send, and port 587

**Decision.** The production guide offers two paths:

- **Gmail with an app password.** The quickest start, around 500 emails a day.
- **Your own domain through Brevo.** Better deliverability, 300 a day on the free plan, and it needs SPF, DKIM and DMARC records in your DNS.

All examples use port 587 with STARTTLS.

**Why.**

- Big providers reject mail sent directly from a fresh server, so you need an established sending service. Gmail is the zero-setup one. A domain on a dedicated service is the long-term one: your own From address, bounce handling, and a reputation you control.
- Hetzner blocks outgoing ports 25 and 465 on new cloud servers, while 587 is open. Using 587 everywhere means the instructions never hit that wall.

---

## N17. The site runs without email configured

**Decision.** Missing email settings don't stop the site from starting. Signups show "Something went wrong" until they're set, and `manage.py check --deploy` warns (`newsletter.W001`) while they're missing.

**Why.** Deploying the newsletter code shouldn't be able to take the whole site down. A deploy check warning makes the gap visible without making it fatal.

---

## N18. The admin side

**Decision.** A **Newsletter** menu with:

- **Subscribers:** search, filter by status, and CSV or Excel export, using Wagtail's built-in model admin.
- **Sent posts:** a read-only list with sent, failed and waiting counts.

Sending requires one permission ("Can add sent post"), which superusers have and which other users' groups can be granted.

**Why.** Wagtail's built-in listing gives search, filters and export without custom screens. The sent-posts list is read-only because the only way to create a send is the post's own page, with its preview and test. One permission keeps "who may email everyone" a single clear switch.
