# Design decisions

Why the project is built the way it is. Each decision says:

- what was decided,
- why,
- why it beats the alternatives,
- what it costs, and when it would be worth revisiting.

"Best" always means best for this project: a personal blog, almost all reads, one small server, and one maintainer who may not touch it for months. Some of these choices would be wrong for a large team or a high-traffic site, and the entries say so where it matters.

## Where the decisions came from

**From you, at the start:**

- Rebuild from scratch, but keep the old design, layout, fonts, spoiler text and other features.
- Plain Tailwind instead of daisyUI.
- `just` instead of a Makefile.
- Separate development and production Dockerfiles together in a root `docker/` folder, with two compose files.
- Wagtail with Nuxt.
- django-environ for settings.
- SQLite, which you asked about; the answer and its limits are in [D1](data-and-configuration.md#d1-sqlite-as-the-database).
- No AI tool credited in commits or pull requests.
- For comments: no email verification to post, only your heart as a like, moderating only in the Wagtail admin, and no emails except opt-in reply alerts ([Comments](comments.md#your-decisions)).

**Made while building:** everything else. That includes rendering on the server rather than a single-page app, which you asked about ([A1](architecture.md#a1-headless-wagtail-with-a-server-rendered-nuxt-site)), the whole newsletter design, and everything about comments beyond your four choices.

The decisions that shouldn't change without discussion are also listed in [`AGENTS.md`](../../AGENTS.md) under "Decisions".

## The principles behind them

1. **One maintainer, long gaps.** Fewer moving parts, well-known tools, and comments that explain why. When two options work, pick the one you can still understand after a year away.
2. **The old look, exactly.** Port, don't redesign, and prove it with screenshots instead of judging by eye.
3. **Everything on one small server.** No service that needs its own server, password or bill: no PostgreSQL, Redis, Celery or Elasticsearch until there's a real need.
4. **Safe in production, zero setup locally.** Production refuses to start without its secrets; development runs with no configuration at all.
5. **Long-supported versions, pinned.** LTS releases, exact lock files, and a calendar for upgrades.
6. **New dependencies must pay for themselves.** The whole newsletter added none, and comments added one: the client for the Akismet spam filter ([M3](comments.md#m3-akismet-checks-every-comment-first)).

## All decisions

### [Architecture](architecture.md)

- [A1. Headless Wagtail with a server-rendered Nuxt site](architecture.md#a1-headless-wagtail-with-a-server-rendered-nuxt-site): a full editor for free, and complete HTML for search engines and link previews.
- [A2. One domain, split by path](architecture.md#a2-one-domain-split-by-path): no CORS, one certificate, normal admin logins.
- [A3. The Nuxt server calls Wagtail directly inside Docker](architecture.md#a3-the-nuxt-server-calls-wagtail-directly-inside-docker): faster page renders that don't depend on public DNS or the certificate.
- [A4. API responses use root-relative URLs](architecture.md#a4-api-responses-use-root-relative-urls): the same response is correct on every machine.
- [A5. Caddy serves uploads, WhiteNoise serves the admin's files](architecture.md#a5-caddy-serves-uploads-whitenoise-serves-the-admins-files): fast file serving, with no shared volume or deploy step.
- [A6. Previews and "View live" open the real site](architecture.md#a6-previews-and-view-live-open-the-real-site): drafts look exactly as they will.

### [Backend](backend.md)

- [B1. The old app names were kept](backend.md#b1-the-old-app-names-were-kept): easy side-by-side comparison with `legacy-ui/`.
- [B2. Wagtail's API for pages, three small views for everything else](backend.md#b2-wagtails-api-for-pages-three-small-views-for-everything-else): each view mirrors an old one exactly.
- [B3. Looking up a page by path returns it directly](backend.md#b3-looking-up-a-page-by-path-returns-it-directly): one request instead of an unreachable redirect.
- [B4. Posts keep their date URLs](backend.md#b4-posts-keep-their-date-urls): old links keep working, and each post has one canonical address.
- [B5. Tags as objects, images with named sizes](backend.md#b5-tags-as-objects-images-with-named-sizes): image sizes decided in one place, and no layout jumps.
- [B6. Site settings are editable, and navigation is a list](backend.md#b6-site-settings-are-editable-and-navigation-is-a-list): any number of links, no code changes.
- [B7. Fields that never did anything were removed](backend.md#b7-fields-that-never-did-anything-were-removed): every admin field changes something.
- [B8. Reading time counts every word](backend.md#b8-reading-time-counts-every-word): it was badly undercounted before.
- [B9. The line-height setting has a "Default" choice](backend.md#b9-the-line-height-setting-has-a-default-choice): the setting works now, and old posts don't change.
- [B10. Spoilers are a custom editor feature stored as plain HTML](backend.md#b10-spoilers-are-a-custom-editor-feature-stored-as-plain-html): portable content that's accessible before JavaScript loads.
- [B11. Search uses Wagtail's database backend](backend.md#b11-search-uses-wagtails-database-backend): no extra service.
- [B12. Every page type shares the SEO fields and the headless setup](backend.md#b12-every-page-type-shares-the-seo-fields-and-the-headless-setup): one implementation for every page.
- [B13. Behaviour visitors could see was copied exactly](backend.md#b13-behaviour-visitors-could-see-was-copied-exactly): order and wording count too.
- [B14. API types written by hand](backend.md#b14-api-types-written-by-hand): a small API doesn't need a code generator.

### [Frontend](frontend.md)

- [C1. The old templates were ported, not redesigned](frontend.md#c1-the-old-templates-were-ported-not-redesigned): identical markup is the surest way to identical pixels.
- [C2. Old quirks were kept, real bugs were fixed](frontend.md#c2-old-quirks-were-kept-real-bugs-were-fixed): the full list of both.
- [C3. Tailwind without daisyUI](frontend.md#c3-tailwind-without-daisyui): you own every style, and old class names still work.
- [C4. The old colours, two themes, and a CSS-only theme switch](frontend.md#c4-the-old-colours-two-themes-and-a-css-only-theme-switch): exact colours, no flicker.
- [C5. The theme is stored where the old site stored it](frontend.md#c5-the-theme-is-stored-where-the-old-site-stored-it): returning readers keep their theme.
- [C6. Three settings that exist only for pixel-perfect output](frontend.md#c6-three-settings-that-exist-only-for-pixel-perfect-output): each closes a measured difference.
- [C7. Components are used by file name only](frontend.md#c7-components-are-used-by-file-name-only): short templates, easy to search.
- [C8. One data layer](frontend.md#c8-one-data-layer): one place decides where requests go, and nothing is fetched twice.
- [C9. Errors look like the old error pages](frontend.md#c9-errors-look-like-the-old-error-pages): matches the old site, and stays safe when the backend fails.
- [C10. Date archives and static pages share the root of the site](frontend.md#c10-date-archives-and-static-pages-share-the-root-of-the-site): the old URL layout.
- [C11. The blog view switch never flashes](frontend.md#c11-the-blog-view-switch-never-flashes): decided in CSS before the first paint.
- [C12. The interactive parts are small, dependency-free Vue](frontend.md#c12-the-interactive-parts-are-small-dependency-free-vue): no UI library, native accessibility.
- [C13. Only rich text from the CMS is inserted as HTML](frontend.md#c13-only-rich-text-from-the-cms-is-inserted-as-html): no injection risk anywhere else.
- [C14. Google Analytics comes from Site settings, in production only](frontend.md#c14-google-analytics-comes-from-site-settings-in-production-only): one place to change it, and no local visits counted.

### [Data and configuration](data-and-configuration.md)

- [D1. SQLite as the database](data-and-configuration.md#d1-sqlite-as-the-database): plenty for a blog, with no database service to run.
- [D2. The database lives in a Docker volume, never in a shared folder](data-and-configuration.md#d2-the-database-lives-in-a-docker-volume-never-in-a-shared-folder): WAL mode needs it.
- [D3. Backups use SQLite's backup command](data-and-configuration.md#d3-backups-use-sqlites-backup-command): copying the live file can give a broken backup.
- [D4. Settings split by environment and read from the environment](data-and-configuration.md#d4-settings-split-by-environment-and-read-from-the-environment): zero setup locally, a loud failure in production.
- [D5. One env file per program](data-and-configuration.md#d5-one-env-file-per-program): secrets reach only the containers that need them.
- [D6. Email settings as separate variables](data-and-configuration.md#d6-email-settings-as-separate-variables): no URL-encoding of passwords.
- [D7. Long-supported versions, pinned twice](data-and-configuration.md#d7-long-supported-versions-pinned-twice): upgrades when you choose, not as surprises.
- [D8. uv for Python, npm for Node](data-and-configuration.md#d8-uv-for-python-npm-for-node): fast, locked installs that are the same everywhere.

### [Infrastructure](infrastructure.md)

- [E1. One server running Docker Compose](infrastructure.md#e1-one-server-running-docker-compose): enough for a blog, with nothing extra to learn.
- [E2. All Docker files together at the root](infrastructure.md#e2-all-docker-files-together-at-the-root): one place for container configuration, and no secrets in images.
- [E3. Lean, locked-down production images](infrastructure.md#e3-lean-locked-down-production-images): reproducible, small, and the app can't rewrite itself.
- [E4. A development stack with live reload](infrastructure.md#e4-a-development-stack-with-live-reload): edit on the Mac, run on the same Linux as production.
- [E5. Caddy in front](infrastructure.md#e5-caddy-in-front): automatic HTTPS in a short config.
- [E6. HTTPS is handled by Caddy alone](infrastructure.md#e6-https-is-handled-by-caddy-alone): internal calls stay plain HTTP, and HSTS starts short.
- [E7. Migrations run when the backend starts](infrastructure.md#e7-migrations-run-when-the-backend-starts): one-command deploys.
- [E8. `just` as the task runner](infrastructure.md#e8-just-as-the-task-runner): readable recipes that list themselves.

### [Newsletter](newsletter.md)

- [N1. Double opt-in](newsletter.md#n1-double-opt-in): only an address's owner can subscribe it.
- [N2. One random token per subscriber, stored in the database](newsletter.md#n2-one-random-token-per-subscriber-stored-in-the-database): old unsubscribe links keep working forever.
- [N3. A signup never reveals who is subscribed](newsletter.md#n3-a-signup-never-reveals-who-is-subscribed): nobody can probe your list.
- [N4. Spam protection without a CAPTCHA](newsletter.md#n4-spam-protection-without-a-captcha): a honeypot and two limits, invisible to people.
- [N5. Confirmation emails go out immediately, post emails through a queue](newsletter.md#n5-confirmation-emails-go-out-immediately-post-emails-through-a-queue): instant feedback, and long sends outside web requests.
- [N6. A database queue and a small worker process](newsletter.md#n6-a-database-queue-and-a-small-worker-process): reliable sending without Redis or Celery.
- [N7. Sending safely: no doubles, retries, pauses, one connection](newsletter.md#n7-sending-safely-no-doubles-retries-pauses-one-connection): a bad password can't burn through the list.
- [N8. Each post is emailed once, on purpose, from the admin](newsletter.md#n8-each-post-is-emailed-once-on-purpose-from-the-admin): sending can't be undone, so it's deliberate.
- [N9. The email is a teaser, not the whole post](newsletter.md#n9-the-email-is-a-teaser-not-the-whole-post): renders everywhere, and readers come to the site.
- [N10. Email HTML built for email apps](newsletter.md#n10-email-html-built-for-email-apps): tables and inline styles, because that's what renders.
- [N11. Unsubscribing: a button on a page, plus one-click headers](newsletter.md#n11-unsubscribing-a-button-on-a-page-plus-one-click-headers): link scanners can't unsubscribe anyone.
- [N12. Confirming happens when the link opens](newsletter.md#n12-confirming-happens-when-the-link-opens): one click, as people expect.
- [N13. It works without JavaScript](newsletter.md#n13-it-works-without-javascript): real forms with a redirect fallback.
- [N14. Deliverability details](newsletter.md#n14-deliverability-details): small things that keep mail out of spam, and no tracking.
- [N15. Mailpit for local testing](newsletter.md#n15-mailpit-for-local-testing): real emails, safely caught.
- [N16. Recommended ways to send, and port 587](newsletter.md#n16-recommended-ways-to-send-and-port-587): Gmail to start, a domain service to grow, and Hetzner's blocked ports avoided.
- [N17. The site runs without email configured](newsletter.md#n17-the-site-runs-without-email-configured): a deploy can't take the site down.
- [N18. The admin side](newsletter.md#n18-the-admin-side): built-in listings, and one permission to send.

### [Comments](comments.md)

- [M1. Readers comment with a name and an email, no account](comments.md#m1-readers-comment-with-a-name-and-an-email-no-account): most readers come once, and the data stays in your database.
- [M2. Every comment is reviewed before it shows](comments.md#m2-every-comment-is-reviewed-before-it-shows): not spam isn't the same as welcome.
- [M3. Akismet checks every comment first](comments.md#m3-akismet-checks-every-comment-first): a filter built for the job, and a failure never loses a comment.
- [M4. A honeypot, a form timer and a limit](comments.md#m4-a-honeypot-a-form-timer-and-a-limit): simple bots stopped before Akismet is asked.
- [M5. No email verification to post a comment](comments.md#m5-no-email-verification-to-post-a-comment): your decision; fewer lost comments, and no mail to strangers.
- [M6. Reply alerts: double opt-in without mailing anyone for an unreviewed comment](comments.md#m6-reply-alerts-double-opt-in-without-mailing-anyone-for-an-unreviewed-comment): a spammer typing a stranger's address causes no email.
- [M7. No email to you about new comments](comments.md#m7-no-email-to-you-about-new-comments): your decision; the admin shows a count instead.
- [M8. Only your heart, no public likes](comments.md#m8-only-your-heart-no-public-likes): your decision; no counters to write or attack.
- [M9. Moderating happens only in the Wagtail admin](comments.md#m9-moderating-happens-only-in-the-wagtail-admin): your decision; the public site never acts with your rights.
- [M10. Every moderation action goes through one module](comments.md#m10-every-moderation-action-goes-through-one-module): Akismet reports and emails can't be skipped.
- [M11. Replies are threaded one level deep](comments.md#m11-replies-are-threaded-one-level-deep): readable on a phone, and one query.
- [M12. Plain text only, with links added by the page](comments.md#m12-plain-text-only-with-links-added-by-the-page): no HTML from strangers ever reaches a page.
- [M13. Visitor details are kept for 30 days at most](comments.md#m13-visitor-details-are-kept-for-30-days-at-most): kept only for Akismet reports, cleaned by the worker.
- [M14. It works without JavaScript](comments.md#m14-it-works-without-javascript): real forms with a redirect fallback.
- [M15. Comments can be switched off everywhere or on one post](comments.md#m15-comments-can-be-switched-off-everywhere-or-on-one-post): stop a spam wave or one touchy post, deleting nothing.
- [M16. The site runs without Akismet configured](comments.md#m16-the-site-runs-without-akismet-configured): a deploy can't take the site down.
- [M17. The admin side](comments.md#m17-the-admin-side): a snippet with filters, row buttons and bulk actions.
- [M18. What was left out on purpose](comments.md#m18-what-was-left-out-on-purpose): Gravatar, accounts, public likes and more, with the reasons.

### [Verification](verification.md)

- [V1. Screenshots of the old and new site, compared pixel by pixel](verification.md#v1-screenshots-of-the-old-and-new-site-compared-pixel-by-pixel): "looks the same" measured, at most 0.003% different.
- [V2. Backend tests](verification.md#v2-backend-tests): 309 fast tests for the logic screenshots can't see.
- [V3. Frontend checks](verification.md#v3-frontend-checks): type check and build, with behaviour checked by hand-run scripts.
- [V4. The newsletter tested end to end on real infrastructure](verification.md#v4-the-newsletter-tested-end-to-end-on-real-infrastructure): a real browser, SMTP server and worker.

## Known gaps

These aren't done yet. Each is small, and each is described in the linked entry.

| Gap | Why it matters | Where |
|---|---|---|
| No scheduled backups | The database now holds subscribers as well as content | [D3](data-and-configuration.md#d3-backups-use-sqlites-backup-command) |
| No CI | Nothing runs the tests, lint, type check and build on each pull request | [V2](verification.md#v2-backend-tests), [V3](verification.md#v3-frontend-checks) |
| No automatic update proposals (Dependabot or Renovate) | Updates rely on the review calendar in `versions.md` | [D7](data-and-configuration.md#d7-long-supported-versions-pinned-twice) |
| The domain is typed five times in production settings | A typo in one copy breaks admin logins or email links | [D5](data-and-configuration.md#d5-one-env-file-per-program) |
| No frontend tests in the repository | Behaviour was checked with scripts that weren't kept | [V3](verification.md#v3-frontend-checks) |
| Newsletter not yet tried with a real mail provider | No credentials were available while building | [V4](verification.md#v4-the-newsletter-tested-end-to-end-on-real-infrastructure) |
| Comments not yet tried with a real Akismet key | No key was available while building; the tests use a stand-in client, so the live connection is untested | [M3](comments.md#m3-akismet-checks-every-comment-first), [`comments.md`](../comments.md#try-it-before-you-trust-it) |
| Comments are not paged | A post loads all its approved comments at once, which is fine for hundreds | [M18](comments.md#m18-what-was-left-out-on-purpose) |

## When a decision changes

Update its entry here in the same pull request: the new choice, why, and what was given up. If it's one of the fixed decisions in `AGENTS.md`, update that too. Keep the "When to revisit" notes current. They're the reminders for future you.
