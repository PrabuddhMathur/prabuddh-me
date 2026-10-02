# Backend

How the Wagtail side is built: the content models, the API and the editing features. See the [index](README.md) for the other areas. The newsletter has [its own page](newsletter.md).

---

## B1. The old app names were kept

**Decision.** The backend uses the old site's app names: `core` (shared blocks, settings, static pages, spoilers), `blog` (posts) and `home` (the home page).

**Why.** You can compare any model or block side by side with `legacy-ui/`, and the admin is organised the way you remember it. New names would make every comparison harder and gain nothing.

---

## B2. Wagtail's API for pages, three small views for everything else

**Decision.** Wagtail's built-in API (v2) serves pages: one page by its path, posts by slug, drafts for previews, and images. Three plain Django views return the remaining JSON:

- `/api/v2/site/`: site settings.
- `/api/v2/posts/`: the post listing with tag and date filters.
- `/api/v2/search/`: search.

They are registered before Wagtail's router so they win.

**Why.** Wagtail's API is good at "give me this page". It has no natural shape for:

- site settings,
- date archives with the old pagination rules (a non-number page shows page 1, a page past the end shows the last page),
- search results with the old type labels.

Each of the three views is a short function that mirrors the matching old Django view line for line, which made matching the old behaviour exact and easy to check.

**Why not the alternatives.**

- **Bending Wagtail's API with filters and custom serializers.** More code, spread across more places, and harder to make behave exactly like the old views.
- **GraphQL (wagtail-grapple).** Another dependency and a schema to maintain, for a site that makes about six kinds of request.
- **Wagtail's new v3 API.** It's a preview in Wagtail 8.0 and isn't in the 7.4 LTS this project uses.

---

## B3. Looking up a page by path returns it directly

**Decision.** `/api/v2/pages/find/?html_path=/about/` returns the page's JSON with status 200, through a small subclass of Wagtail's pages endpoint in `config/api.py`.

**Why.** Wagtail's own `find` answers with a redirect to the page's detail URL, and that URL is an absolute address built from the public site URL. From inside Docker that address isn't reachable, and even where it is, it costs a second request. Returning the page directly makes rendering a page one request instead of two.

---

## B4. Posts keep their date URLs

**Decision.** A post's address is `/YYYY/MM/DD/slug/`, built in `BlogPage.get_url_parts()` from the post date. The frontend loads a post by its slug and returns a 404 if the date in the URL doesn't match the post. A post's tree path (`/slug/`) permanently redirects (301) to its date URL.

**Why.**

- The old site used these URLs, so existing links, bookmarks and search results keep working.
- Wagtail builds every link to a post from this one method. "View live", previews, search results and links inside rich text all get the date URL without any extra code.
- Checking the date stops the same post from appearing at many addresses (`/2020/01/01/slug/`, `/2021/…`), which search engines treat as duplicate content.
- The 301 makes the date URL the only official address. The old site answered at both, another source of duplicate content.

**Why not the alternatives.** Wagtail's default tree URLs (`/slug/`) would break every old link. A routable blog index page that handles the date URLs was what the old code once had, but that model was deleted before the rebuild. The date archives are now plain frontend routes, which is simpler.

---

## B5. Tags as objects, images with named sizes

**Decision.**

- Tags come back as `{ name, slug }`, not just names.
- Images come back with named renditions for each place they're used, each with its real width and height, for example `card` (800×450 crop), `list` (400×300 crop), `display` (1200 wide), `full` (2400 wide) and `og` (1200×630, for link previews).

**Why.**

- Tag links need the slug.
- Decisions about image sizes live in one place, the backend. The frontend never assembles image URLs; it asks for a size by name.
- Wagtail never enlarges images, so a rendition can be smaller than its name suggests. Sending the real dimensions lets the browser reserve the right space, so the page doesn't jump while images load.

---

## B6. Site settings are editable, and navigation is a list

**Decision.** Site, header, footer and author settings are Wagtail settings with the old names, edited under **Settings** in the admin. The header menu and the footer links are lists of `{ text, url }` items, replacing the old five fixed pairs of "link N text / link N URL" fields. The old default links are kept.

**Why.** Everything that changes the site's chrome is editable without code. A list holds any number of links in any order, with no empty slots to leave blank and no limit of five.

---

## B7. Fields that never did anything were removed

**Decision.** Fields that no live template ever displayed were not carried over, for example:

- `SiteSettings`: tagline and contact fields.
- `HomePage`: comments switch and custom CSS class. (That switch did nothing. Comments now exist as a real feature, built from scratch with their own settings: see [M15](comments.md#m15-comments-can-be-switched-off-everywhere-or-on-one-post).)
- `BlogPage`: related-posts switch.
- Blocks: unused colour and style options.
- The unfinished "citation" editor feature, whose script never existed.

**Why.** Every field in the admin should change something on the site. Dead fields confuse whoever edits, and they're code to maintain and migrate forever. Nothing visible was lost, because no live template ever used them.

---

## B8. Reading time counts every word

**Decision.** When a post is saved, its reading time is calculated as `max(1, round(words / 200))` minutes. The count covers the intro and all text in the body, including rich text, headings, quotes, captions and button text. `manage.py recalculate_reading_times [--dry-run]` (or `just reading-times`) recalculates all posts.

**Why.** The old code skipped the text inside rich-text blocks, which is most of a post, so nearly every post claimed about one minute. Storing the number when the post is saved keeps listings fast, because nothing is counted per request.

---

## B9. The line-height setting has a "Default" choice

**Decision.** Posts have a line-height option whose first choice, **Default (1.75)**, applies no override and is the default for new posts. The other choices (1.5, 1.55, 1.625, 1.8, 2.0) now really change paragraph spacing in the post body.

**Why.** On the old site this setting never worked: the CSS class it relied on was never generated, so every post rendered at 1.75. A "Default" choice that changes nothing keeps every existing post looking exactly as it did, while the other choices finally do what they say.

---

## B10. Spoilers are a custom editor feature stored as plain HTML

**Decision.** The rich-text editor has a 👁 spoiler button. Spoiler text is stored as `<span class="spoiler" data-spoiler="true">…</span>`, exactly as on the old site. The frontend adds the click and keyboard behaviour. It also adds the accessibility attributes (`role="button"`, `tabindex`, `aria-pressed`, a label) while rendering on the server.

**Why.**

- Wagtail 7.4 has no spoiler feature. This was checked in the installed package before building one.
- Storing a tagged `<span>` keeps the content portable: it's readable HTML even without this frontend, and existing spoilers carried over unchanged.
- Adding the attributes during server rendering means spoilers work with a keyboard and screen readers before any JavaScript loads.

---

## B11. Search uses Wagtail's database backend

**Decision.** Search runs on Wagtail's built-in database backend, which uses SQLite's full-text search. Results are in relevance order, 10 per page. The site's root page is excluded, and results show the old type labels ("Blogpage").

**Why.** It needs no extra service, and it's plenty for a blog with hundreds of posts.

**When to revisit.** If search quality starts to matter more (typo tolerance, better ranking), move to PostgreSQL's search or a search service. That's one of the reasons to leave SQLite listed in [D1](data-and-configuration.md#d1-sqlite-as-the-database).

---

## B12. Every page type shares the SEO fields and the headless setup

**Decision.** One abstract mixin, `SEOFields`, gives every page type the same fields: meta description, keywords, Open Graph title, description and image. Every page model also includes `HeadlessMixin`.

**Why.** The frontend's `usePageSeo` reads the same fields from any page, so SEO behaves identically on the home page, posts and static pages. A new page type gets both features by adding two mixins.

---

## B13. Behaviour visitors could see was copied exactly

**Decision.** Where the old site's behaviour was visible, it was reproduced:

- Featured posts on the home page appear in the order they were created.
- "Previous post" means the next older post, "Next post" the next newer one.
- Search labels read "Blogpage".
- The editor validation rules were kept: no future post dates, and a button needs both text and a link.

**Why.** "Exactly like the old site" covers order and wording, not just colours and spacing.

---

## B14. API types written by hand

**Decision.** The frontend describes every API response in `frontend/app/types/api.ts` by hand. AGENTS.md requires changing it together with the backend's `api_fields` and views.

**Why.** The API is small (about fifteen shapes). Generating types would mean producing an OpenAPI schema and running a code generator, which adds another tool and build step. Wagtail doesn't publish a usable schema for StreamField blocks anyway.

**Cost.** The two can drift apart. The typecheck catches the frontend misusing its own types, but not the backend changing a shape. The rule "change both in the same pull request" is the safeguard.
