# Frontend

How the Nuxt site is built so it looks and behaves exactly like the old one. See the [index](README.md) for the other areas, and [verification](verification.md) for how "exactly" was measured.

---

## C1. The old templates were ported, not redesigned

**Decision.** Each Vue component is a line-by-line port of an old Django template: the same elements, nesting, classes, text and SVG icons, and even the same line breaks. The old templates are kept in `legacy-ui/` as the reference.

**Why.** You asked for the same look. The surest way to get identical pixels is identical markup with identical CSS values. Porting also makes every change checkable: you put the component next to its old template and compare.

**Why not the alternative.** Rebuilding the look "by eye" in fresh markup drifts by a few pixels here and a different line break there. Those differences add up to a site that feels slightly off, and you can't easily tell where.

**Cost.** Some markup is written the way the old site needed rather than how you'd write it fresh. A redesign later is a separate project; the port doesn't block it.

---

## C2. Old quirks were kept, real bugs were fixed

**Decision.** "Exactly like the old site" means what visitors actually saw. Accidental details that were visible are kept. Things that were broken behind the scenes are fixed, but only where the fix doesn't change the default look.

Kept (visitors saw these):

| Quirk | Why it looks that way |
|---|---|
| Home page post cards have no image or excerpt | The old template asked for fields that didn't exist |
| Tag and date archives have no breadcrumbs | The old breadcrumb sat outside the page's content block |
| Quotes use Georgia-style serif, not Hedvig | The old font setting never reached Tailwind |
| At most 3 tags per list, even under a post | The old tag component defaulted to 3 |
| The 500 page has no header or footer, is always light and uses the system font | It was a standalone page with no theme script or web font |
| Search badges say "Blogpage", "Staticpage" | The old page title-cased the model name |
| The header hides when you scroll down past 100 px and returns when you scroll up, on every screen size | An inline script overrode the mobile-only script |
| A hero block's "large" height has no minimum height | Its class name didn't exist |
| A call-to-action on the primary colour has almost invisible text | The old colours did that; changing it is a design decision for you |

Fixed (broken, and fixing them doesn't change the default look):

| Fix | Before |
|---|---|
| A hero block's background image shows | The old CSS targeted a class the block didn't have |
| The post line-height setting works ([B9](backend.md#b9-the-line-height-setting-has-a-default-choice)) | It never had any effect |
| The header search box finds things | It sent `q`, but the search page read `query`. The search page now accepts both |
| Search shows the total number of results | It showed how many were on the current page |
| Reading time counts all words ([B8](backend.md#b8-reading-time-counts-every-word)) | It skipped rich text |
| The newsletter form works ([newsletter](newsletter.md)) | It posted to `#` and failed |
| Google Analytics uses the ID in Site settings, in production only | An ID was also hard-coded in the template |
| Search leaves out the site's root page | It could show up as a result |
| `/blog/author/<anything>/` redirects to `/blog/` | The old code had this redirect, but it was never connected to a URL, so it showed a 404 |
| A post's `/slug/` address redirects to its date URL ([B4](backend.md#b4-posts-keep-their-date-urls)) | Both addresses answered, which is duplicate content |

**Why.** Silently fixing a visible quirk would be a redesign decision, and that's yours to make. Fixing something that never worked doesn't change the look, so it only makes the site better.

---

## C3. Tailwind without daisyUI

**Decision.** daisyUI is gone, as you asked. Each daisyUI class was replaced with plain Tailwind utilities that produce the same computed style, measured from the old site's compiled CSS. Buttons, inputs and the search pagination (`.btn`, `.input`, `.join` and their size variants) are hand-written classes in `main.css`, so templates keep the old class names. The colour tokens keep daisyUI's names (`bg-base-100`, `text-base-content/60`, `border-primary`) with the old values.

**Why.**

- You own every style. A daisyUI major version can't change the site's look behind your back.
- There's one dependency fewer to update.
- Keeping the class and colour names means old templates port almost word for word.
- Buttons and inputs became classes rather than repeated utilities because they appear in many places with local overrides. Putting them in the `components` layer, below Tailwind's utilities, reproduces daisyUI's rule that a utility on the same element wins.

**Why not the alternatives.**

- **Keeping daisyUI 5.** Against your wish, and it ties the look to their release cycle.
- **Restyling from scratch with fresh utilities.** It would drift from the old look ([C1](#c1-the-old-templates-were-ported-not-redesigned)).

**Cost.** `main.css` holds about a page of hand-written button and input styles, including hover, active, focus and disabled states, which you now maintain yourself.

---

## C4. The old colours, two themes, and a CSS-only theme switch

**Decision.** The colour values are exactly what the old site rendered: daisyUI's `light` and `dim` themes as overridden by the old site's own theme blocks. Light is the default. Dim values override them under `[data-theme="dim"]`, and a custom `dim:` variant styles theme-specific bits, such as showing the moon icon in dim.

**Why.** The values are exact for parity. The `dim:` variant is plain CSS, so the HTML rendered on the server is already right for the theme. Nothing waits for JavaScript to decide which icon to show, which avoids flicker and mismatches when the page hydrates.

---

## C5. The theme is stored where the old site stored it

**Decision.** `@nuxtjs/color-mode` keeps the reader's choice in `localStorage` under the key `theme`, with the values `light` and `dim`, and sets `<html data-theme="…">`. These are the same key, values and attribute as the old site. The server renders `light`, and the module's small inline script applies a saved choice before the first paint.

**Why.** Readers who chose dim on the old site still get dim after the rebuild, without a flash of the light theme on load.

---

## C6. Three settings that exist only for pixel-perfect output

**Decision.** Three settings exist purely so the output matches the old site to the pixel:

- **`vue.compilerOptions.whitespace: 'preserve'`.** Vue normally drops whitespace that contains a line break between two elements. Browsers render that whitespace as a space, and the old HTML relied on it, for example in "Home / Blog" breadcrumbs. Without it, the newsletter card was 3.23 px narrower.
- **`postcss.plugins.cssnano: false`.** Nuxt's extra CSS minifier rounded Tailwind's calculated line heights (20 px became 19.984 px), shifting text by fractions of a pixel. Tailwind and Vite still minify the CSS.
- **`--font-sans` pinned to Tailwind 4.1's font list.** Tailwind 4.3 changed its default sans-serif fonts. This only affects the 500 page.

**Why.** Each one closed a difference measured in the screenshot comparison. AGENTS.md marks them as "don't remove".

---

## C7. Components are used by file name only

**Decision.** Components live in folders for tidiness (`listing/`, `blocks/`, `site/`…) but are used by file name alone, as `<PostCard>` rather than `<ListingPostCard>`. Every file name is therefore unique.

**Why.** Templates stay short and close to the old `{% include %}` names. A component can move to another folder without renaming every usage, and searching for `PostCard` finds both the file and every place it's used.

---

## C8. One data layer

**Decision.**

- **`$api`** (in `plugins/api.ts`) is the only HTTP client. On the server it calls the backend directly (`NUXT_BACKEND_URL`); in the browser it calls `/api/` on the same domain.
- **`useApi`** wraps Nuxt's `useFetch` with `$api`.
- **`useSiteSettings`** fetches the site settings once per page load under a fixed key, and reuses them on later page changes in the browser.
- **`usePageSeo`** reproduces the old `seo_meta.html`: title, the description fallbacks, Open Graph and Twitter tags, and the canonical link.

**Why.**

- One place decides where requests go.
- `useFetch` hands the server's data to the browser inside the page, so nothing is fetched twice when the page hydrates.
- Settings aren't requested again on every click.
- SEO tags come out identical to the old site's.

**Why not the alternative.** A state library such as Pinia isn't needed. Every page's data is fetched for that page on the server, and nothing is shared or edited in the browser.

---

## C9. Errors look like the old error pages

**Decision.** A "not found" from the API becomes the old 404 page, inside the normal header and footer. Any other error shows the old 500 page on its own: no header or footer, light theme, system font.

**Why.** It matches the old site. A failing backend also shouldn't produce a half-working layout, because the header and footer need the backend too.

---

## C10. Date archives and static pages share the root of the site

**Decision.** The date routes match only digits: `/2025/`, `/2025/03/`, `/2025/03/03/` and `/2025/03/03/slug/` (for example `/:year(\d{4})`). Everything else at the root, such as `/about/`, falls through to the static-page route.

**Why.** It keeps the old URL layout, where date archives and pages like About both sit directly under `/`, without the two kinds of route catching each other's URLs.

---

## C11. The blog view switch never flashes

**Decision.** The listing's masonry/list choice is kept in `localStorage['blog-view-mode']`, the old key and values. A tiny script in the page head copies it onto `<html data-blog-view>` before the first paint. Both views are always in the HTML, and CSS shows the chosen one.

**Why.** A switch done by JavaScript after the page loads shows masonry first and then jumps to the list on every visit. Deciding in CSS before the first paint means the right view appears immediately.

---

## C12. The interactive parts are small, dependency-free Vue

**Decision.**

- **Gallery:** the browser's own `<dialog>` element. Image blocks open it through Vue's provide/inject.
- **Spoilers:** one click and keyboard handler on the rich-text container.
- **Header:** hides and shows on scroll through a passive, frame-throttled listener.
- **Menus:** close on an outside click, Escape, or a page change. The mobile menu reports `aria-expanded`.

**Why.** No UI library to install or update. The native dialog brings Escape-to-close, focus handling and the backdrop for free, and it behaves correctly for screen readers.

---

## C13. Only rich text from the CMS is inserted as HTML

**Decision.** `v-html` is used only for rich text that comes from the CMS. Internal links inside that text navigate within the app instead of reloading the page.

**Why.** Only trusted, editor-written content is ever inserted as raw HTML, which keeps cross-site scripting risks out of everything else. In-site links stay fast.

---

## C14. Google Analytics comes from Site settings, in production only

**Decision.** The analytics script loads only in production builds, and only when an ID is set in **Settings → Site Settings**.

**Why.** The old site also hard-coded an ID in its template. Now there's one place to change it, and your own local browsing never counts as visits.
