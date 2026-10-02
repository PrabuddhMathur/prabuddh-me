# Verification

How the rebuild was checked: that it looks exactly like the old site, and that the code works. See the [index](README.md) for the other areas.

---

## V1. Screenshots of the old and new site, compared pixel by pixel

**Decision.** "Exactly like the old site" was measured, not judged by eye:

1. The old site was run locally from git history (commit `49cda9c`).
2. The old site and the new one were loaded with the same demo content: posts, images, pages and settings.
3. A Playwright script took screenshots of every kind of page at three sizes (phone 390×844, tablet 768×1024, desktop 1280×800) in both themes. It added the interactive states: a revealed spoiler, the open gallery and its next image, the mobile menu, the view-switch menu, and the header hidden after scrolling. That's 144 screenshots per site.
4. A pixel comparison (pixelmatch) reported the share of differing pixels for each pair, and showed old, new and a difference image side by side.
5. Buttons and inputs were also compared by computed CSS values in their hover, pressed, focused and disabled states, which screenshots don't show.

Taking the old site's screenshots twice gave zero differing pixels, so any difference between old and new was real, not noise. At the end, every one of the 144 screenshots matched within 0.003%. Later test pages for each content block matched as well, apart from the hero block's background image, which now shows on purpose ([C2](frontend.md#c2-old-quirks-were-kept-real-bugs-were-fixed)). The newsletter work re-ran all 162 screenshots, and none changed.

**Why.** Eyes miss a 1-pixel shift, a slightly different line height, or a missing space between two buttons. Numbers don't. The comparison turned "it looks the same" into a pass/fail check, and it caught real problems that review wouldn't have: the whitespace and CSS-minifier issues in [C6](frontend.md#c6-three-settings-that-exist-only-for-pixel-perfect-output) were both found this way.

**Not kept.** The screenshot setup ran from a temporary folder and isn't in the repository, because it needs the old site running from git history. Any visual change from now on will be deliberate, so the old site is no longer the reference. If you want protection against accidental visual changes later, the lighter version is to compare the new site with its own earlier screenshots. That would be a small tool under `tools/`.

---

## V2. Backend tests

**Decision.** 309 Django tests across `core`, `blog`, `newsletter` and `comments`, run with `just test`. They cover:

- **API shapes and edge cases:** ordering, pagination, tag and date filters, 404s, search.
- **Editor features:** the spoiler round-trip through the editor's converter, and reading time over rich text.
- **The newsletter:**
  - every signup case and the token rules,
  - the email headers and links,
  - the queue and the worker's failure handling: retries, pauses, double-send protection and reconnects,
  - admin permissions and the deploy check.
- **The comments:**
  - the public endpoints: the list's shape, threading and hidden replies, every validation error, the honeypot, the form timer, the limit, and the form-post redirects,
  - Akismet through a stand-in client: each verdict, the details sent, and every kind of failure,
  - moderation and the emails it causes: reply-alert rules, reports to Akismet, and a failing email that must not undo an approval,
  - the confirm and stop endpoints, the emails' links and headers, the cleanup, and the worker's hourly run of it,
  - the admin: the list, row and bulk actions, permissions, the edit and reply pages, and the waiting count.
- **The shared form and email code.** It moved out of the newsletter into `core` for the comments. The newsletter's own tests passed unchanged, and its confirmation and post emails (text and HTML) were rendered before and after and compared: they were identical.

**Why.** Backend logic is where silent bugs hide, and Django tests are fast and need no running servers. A wrong JSON shape or a double-sent email doesn't show up in a screenshot.

---

## V3. Frontend checks

**Decision.** The type check (`vue-tsc`) and the production build must pass. During development, behaviour was also tested with Playwright scripts against a running site: keyboard use, error states, the forms with JavaScript turned off, and the theme and view switches.

**Why this balance.** The frontend is mostly markup, and its correctness is visual, which V1 covers. Types catch wrong data access, and the build catches broken imports and templates.

**Gap.** None of the Playwright behaviour scripts are in the repository, so there are no automated frontend tests. If the frontend gains more logic, a few end-to-end smoke tests (home loads, a post loads, signup shows the success message) would be the first to add.

---

## V4. The newsletter tested end to end on real infrastructure

**Decision.** Besides the unit tests, the newsletter ran for real: a browser, the Nuxt and Wagtail servers, the worker, and a real SMTP server (Mailpit). Covered:

- signup, the confirmation email, and confirming;
- repeated and invalid signups, and the honeypot;
- both forms with JavaScript off;
- a test send and a real send from the admin, with the delivered email's headers, links and image checked;
- unsubscribing from the page and with one click;
- the mail server going down mid-send, after which every email was sent exactly once;
- someone unsubscribing between queueing and sending.

The Docker dev stack was checked with the worker and Mailpit, and the production images were built, with the worker run inside one.

**Why.** Unit tests can't see a wrong link inside an email, a broken hand-off between the two apps, or a proxy that behaves differently from Caddy. This run found exactly that last kind of bug: the dev proxy followed redirects that Caddy passes on. It was fixed before merging.

**Not tested.** Sending through a real Gmail or Brevo account; no credentials were available. The STARTTLS connection on port 587 is configured but was never exercised. Your first `sendtestemail` in production ([guide, step 4](../newsletter-production.md#4-test-the-email-connection)) is that test.
