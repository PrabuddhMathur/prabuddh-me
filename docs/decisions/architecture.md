# Architecture

How the pieces fit together: what runs where, and how requests travel. See the [index](README.md) for the other areas.

Each decision has the same parts: what was decided, why, why it beats the alternatives for this project, and what it costs.

---

## A1. Headless Wagtail with a server-rendered Nuxt site

**Decision.** Wagtail does two jobs only: the admin where you write, and a JSON API. A separate Nuxt 4 app renders every public page on the server (SSR) and then takes over in the browser, so moving between pages doesn't reload them.

**Why.**

- Wagtail gives you a mature editor for free: StreamField blocks, an image library with automatic resizing, revisions, scheduled publishing, previews and editable site settings. Building that yourself would take months.
- Nuxt gives the site a modern component setup. The interactive parts (the gallery, spoilers, the theme switch, menus, the view switcher, the newsletter form) are cleaner as Vue components than as the old template-plus-script mix.
- Server rendering sends every page as complete HTML. Search engines and link previews (WhatsApp, Slack, LinkedIn, X) read the title, description and image without running any JavaScript. Readers see text straight away, even on a slow phone.

**Why not the alternatives.**

- **A single-page app (SPA), which you asked about.** An SPA sends an almost empty page and builds it in the browser. Most link-preview bots never run that JavaScript, so a shared post would show no title or image. Google does render JavaScript, but later and less reliably. Phones also wait longer before they see any text. SSR gives full HTML first and SPA-style navigation afterwards, so you get both.
- **Wagtail rendering the pages itself, as the old site did.** That's the simplest stack, with one app. But you wanted a fresh frontend without daisyUI, and the interactive parts are where the old site had grown brittle.
- **A static site (`nuxt generate`).** Fast and cheap to host, but every publish would need a rebuild and redeploy (a webhook, a build machine, waiting). Previews, search and the newsletter signup need a server anyway. With SSR, publishing in the admin is live immediately.
- **A hosted headless CMS (Contentful, Sanity, Strapi Cloud).** Monthly cost, a vendor's limits, and your content in someone else's database. Wagtail is Python like the old site, free, self-hosted, and has long-term-support releases.

**Costs and when to revisit.** There are two apps to run and deploy instead of one, and the frontend's API types must be kept in step with the backend by hand (see [B14](backend.md#b14-api-types-written-by-hand)). If traffic ever grows a lot, the next step is caching rendered pages in Nuxt, not changing the architecture.

---

## A2. One domain, split by path

**Decision.** Everything is served from `prabuddh.in`. Caddy sends `/admin/`, `/api/`, `/documents/` and `/static/` to Wagtail, serves `/media/` itself from the uploads volume, and sends every other path to Nuxt.

**Why.**

- The browser calls `/api/...` on the same origin, so there is no CORS setup and no extra preflight request before each API call.
- Login cookies and CSRF protection for the admin work as in any normal Django site.
- One TLS certificate and one domain to manage.
- Links stored in content (images, documents, internal pages) stay valid whichever app serves them.

**Why not the alternatives.**

- **An API subdomain (`api.prabuddh.in`).** It needs CORS headers, CSRF trusted origins and cross-origin cookie settings, plus a second certificate. That's three things to get right and keep right, for no gain.
- **Nuxt forwarding API calls itself.** Every API call and every image would pass through Node first. That's slower, and it ties up the Nuxt server with file transfers.

**Costs.** Nuxt can't use those path prefixes for its own pages. It doesn't need to: the newsletter pages, for example, live at `/newsletter/`. In development the Nuxt dev proxy plays Caddy's role, including passing redirects through to the browser (see [N13](newsletter.md#n13-it-works-without-javascript)).

---

## A3. The Nuxt server calls Wagtail directly inside Docker

**Decision.** When Nuxt renders a page on the server, it fetches data from `http://backend:8000` over Docker's internal network (`NUXT_BACKEND_URL`). Browsers use `/api/` through Caddy.

**Why.**

- Each page render skips a trip out to the public internet and back through TLS.
- It works before DNS points at the server, and while a certificate is being renewed.
- The busiest path (rendering pages) has the fewest moving parts.

**What it implies.** Production `ALLOWED_HOSTS` includes `backend`, the name Docker gives the container. Django's own HTTP-to-HTTPS redirect is off, because it would redirect these internal plain-HTTP calls. Caddy redirects visitors instead (see [E6](infrastructure.md#e6-https-is-handled-by-caddy-alone)).

**Why not the alternative.** Calling `https://prabuddh.in/api/` from inside the server loops out through Caddy. It is slower and fails whenever public DNS or the certificate has a problem.

---

## A4. API responses use root-relative URLs

**Decision.** Page, image and media URLs in API responses are paths such as `/2025/01/10/my-post/` and `/media/images/photo.jpg`, never full `https://…` addresses.

**Why.** The same response is correct on `localhost:3000`, inside Docker and on `prabuddh.in`. Wagtail's own absolute URLs (`detail_url`, `html_url`) are built from settings that differ per environment, and they were wrong inside Docker. The frontend adds the domain only where a full address is required (canonical links, Open Graph tags), using `NUXT_PUBLIC_SITE_URL`. The newsletter emails do the same with `FRONTEND_URL`.

---

## A5. Caddy serves uploads, WhiteNoise serves the admin's files

**Decision.** Caddy serves `/media/` (uploaded images and files) straight from the `backend_media` volume, mounted read-only. Django serves media only in development. The admin's own CSS and JavaScript (`/static/`) are served by WhiteNoise from inside the backend image, with hashed, pre-compressed file names.

**Why.**

- Caddy serves files efficiently and never ties up a Django worker for an image download.
- WhiteNoise means the backend image carries its own static files. There's no shared static volume and no `collectstatic` step at deploy time.
- The hashed names mean browsers never keep stale admin CSS after an upgrade.

**Why not the alternatives.**

- **Django serving media in production.** Slow, and Django's documentation advises against it.
- **Object storage (S3 or similar).** Another account, more credentials and a monthly bill, for a site whose uploads fit on the server's disk.

**When to revisit.** Move to object storage, possibly with a CDN, if uploads outgrow the disk or you ever run more than one server.

---

## A6. Previews and "View live" open the real site

**Decision.** Every page model includes `HeadlessMixin` from `wagtail-headless-preview`. Preview in the admin opens the Nuxt page `/preview/?content_type=…&token=…`, which fetches the draft from `/api/v2/page_preview/` and renders it with the same components as the live page. "View live" sends you to the page's URL on the Nuxt site.

**Why.** You see a draft exactly as readers will. The package is maintained by Torchbox, the company behind Wagtail, so you're not maintaining custom preview code.

**Why not the alternatives.**

- **No preview.** You would publish blind.
- **Custom preview tokens.** More security-sensitive code to maintain.

**Details.** The preview page is marked `noindex`. Preview tokens expire after about a day, after which the link shows "not found".
