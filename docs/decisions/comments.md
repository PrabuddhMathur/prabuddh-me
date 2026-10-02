# Comments

Why comments work the way they do. For running them, see [`comments.md`](../comments.md) and [`local-development.md`](../local-development.md#try-the-comments-locally). See the [index](README.md) for the other areas.

The guiding idea: a personal blog's comments are "a reader says something, and you decide whether it appears". Readers shouldn't need an account. Spam shouldn't reach the page or waste your time. Nobody should get an email they didn't ask for. And it should add no service to run, and no screen outside the Wagtail admin you already use.

## Your decisions

Four choices came from you. They are requirements, not options: ask before changing them.

| Decision | Entry |
|---|---|
| No email verification link to post a comment (for now) | [M5](#m5-no-email-verification-to-post-a-comment) |
| Likes are only your heart, shown as a badge. No public like buttons or counts | [M8](#m8-only-your-heart-no-public-likes) |
| Moderating, liking and replying as the author happen only in the Wagtail admin. The public site never knows who is logged in | [M9](#m9-moderating-happens-only-in-the-wagtail-admin) |
| The only emails are opt-in reply alerts. No email to you about new comments, and no "your comment is live" email except as part of the reply-alert confirmation | [M6](#m6-reply-alerts-double-opt-in-without-mailing-anyone-for-an-unreviewed-comment), [M7](#m7-no-email-to-you-about-new-comments) |

Everything else was decided while building.

---

## M1. Readers comment with a name and an email, no account

**Decision.** A reader writes a name, an email address and the comment. The address is never shown anywhere on the site. There are no accounts, no Gravatar pictures and no website field. The comment system is part of this project (a Django app, `backend/comments/`, and a few Vue components), built the way the newsletter was.

**Why.**

- Most readers of a personal blog come once. A login, or even a registration step, loses most of the comments you would have had.
- The data stays in your own SQLite database, with no tracking script on the page.
- The comment form and thread can use the site's own components and colours, so they look like the rest of the site.
- It reuses what already exists: the Wagtail admin for moderation, the newsletter's form handling, and its email code.

**Why not the alternatives.**

- **Disqus and similar hosted systems.** They load heavy third-party scripts, track readers, show ads on free plans, and can't be made to look like this site.
- **Giscus or Utterances.** They store comments in GitHub, so only readers with a GitHub account can comment. Most of your readers don't have one.
- **A self-hosted comment server (Remark42, Commento).** It works, but it's another service to run, update and back up, which [the principles](README.md#the-principles-behind-them) rule out.
- **No comments, only a "reply by email" link.** Simple, but readers can't see each other's thoughts, and email replies need you to copy them into the site by hand.

**Costs.** One more app to maintain: models, public endpoints, admin screens and two emails. And a spam problem to manage ([M2](#m2-every-comment-is-reviewed-before-it-shows), [M3](#m3-akismet-checks-every-comment-first), [M4](#m4-a-honeypot-a-form-timer-and-a-limit)).

**Limits.** A name is 1 to 80 characters. A comment is 1 to 5,000 characters of plain text ([M12](#m12-plain-text-only-with-links-added-by-the-page)). The email address is checked for a valid format, stored in lower case, and kept only to send reply alerts ([M6](#m6-reply-alerts-double-opt-in-without-mailing-anyone-for-an-unreviewed-comment)).

---

## M2. Every comment is reviewed before it shows

**Decision.** A new comment is "Waiting for review". It becomes public only when you approve it in the admin. This applies to every commenter, every time.

**Why.**

- Not being spam isn't the same as being welcome. Abuse, off-topic comments and strangers' personal details all pass a spam filter.
- Search engines index comments. A bad comment that is live for a day can be indexed.
- A personal blog gets few comments, so the queue is short. The admin shows how many are waiting ([M7](#m7-no-email-to-you-about-new-comments)).

**Why not the alternatives.**

- **Publish first, remove later.** Anything bad is public until you notice it.
- **Auto-approve people who were approved before.** It would be a rule based on the email address, and nobody proves they own the address they type ([M5](#m5-no-email-verification-to-post-a-comment)), so anyone could borrow a trusted address.
- **Let the spam filter decide alone.** Filters make mistakes in both directions. Akismet's verdict sorts the queue ([M3](#m3-akismet-checks-every-comment-first)); it never publishes anything.

**Costs.** You have to do something, and a comment appears hours or days after it was written. The form tells the reader this: "Your comment is waiting for review and will appear once it's approved."

**When to revisit.** If the queue becomes a chore, the next step is to publish comments Akismet calls "not spam" and review only the doubtful ones. That's a small change in one place (the Akismet branch of the public endpoint), but it gives up the guarantee that nothing appears without your say-so.

---

## M3. Akismet checks every comment first

**Decision.** When a comment is posted, the backend asks [Akismet](https://akismet.com), a spam-filtering service, whether it is spam. The answer decides where the comment starts:

| Akismet says | What happens |
|---|---|
| Not spam | Saved as "Waiting for review", Akismet verdict "Not spam" |
| Spam | Saved as "Spam" (hidden, kept 30 days), verdict "Spam" |
| Blatant spam (it asks the site to discard it) | Not stored at all |
| An error, a timeout, or no key | Saved as "Waiting for review", verdict "Not checked" |

When you approve a comment Akismet called spam, or mark a missed one as spam, the backend tells Akismet, which improves its answers over time. The check uses the `akismet` library, with its settings written out in code (the key from `AKISMET_API_KEY`, the site address from `FRONTEND_URL`), a 4-second timeout, and no "is my key valid" request before every comment.

**Why.**

- Without a filter the queue fills with spam, and one person has to read all of it. Akismet is built for exactly this, and it learns from a very large number of sites.
- Keeping Akismet's spam instead of deleting it means a false alarm can be rescued from the Spam list, and approving it teaches Akismet.
- A problem with Akismet (down, slow, wrong key) must never lose or block a comment. So every error is logged as a warning and the comment goes to review as "Not checked". The poster waits at most 4 seconds.
- It's free for personal blogs.

**Why not the alternatives.**

- **A CAPTCHA.** The reasons are the same as in [N4](newsletter.md#n4-spam-protection-without-a-captcha): a third-party script, a slower page and annoyed readers.
- **Rules of our own** (too many links, banned words). They need constant upkeep and catch less.
- **The raw HTTP calls instead of the library.** Akismet's API is four endpoints, so this is possible. But the library already handles the details that are easy to get wrong: the discard hint, error responses and a key the service rejects. A mistake there quietly lets spam in or loses comments. The library is small, typed, BSD-licensed and written by a well-known Django maintainer. Why this version: [`versions.md`](../versions.md#akismet).

**Costs.**

- **A third party sees every comment.** Akismet receives the commenter's name, email, text, IP address and browser, plus the post's address. The form says so under the button, with a link to Akismet's privacy page.
- **It's free only for non-commercial sites.** Ads, affiliate links, donations or sales on the blog would need a paid plan. The setup is in [`comments.md`](../comments.md#get-an-akismet-key).
- **Five new Python packages:** the library plus the HTTP client it needs (httpx and its helpers). It's the only dependency comments added ([principle 6](README.md#the-principles-behind-them)).

**When to revisit.** If Akismet's terms or price change, or if spam keeps reaching the review queue anyway.

---

## M4. A honeypot, a form timer and a limit

**Decision.** Three light defences in front of Akismet, in the same family as [N4](newsletter.md#n4-spam-protection-without-a-captcha):

- **A honeypot.** A hidden field called `website` that people never see. A comment with it filled in is thrown away.
- **A form timer.** When the page loads, the backend hands the form a signed time stamp. A comment posted with no stamp, a forged one, or one younger than 3 seconds is thrown away. The stamp never expires, so a tab left open overnight still works.
- **A limit per visitor.** At most 10 comments per IP address per hour (`COMMENTS_POST_LIMIT`). The IP comes from Caddy's `X-Real-IP` header.

A comment thrown away by the first two defences gets the normal "waiting for review" answer, so a bot can't tell it failed and tune its attack. Only the limit says "too many" (HTTP 429).

**Why.**

- Simple bots fill every field and post instantly, and these catch them before Akismet is asked, which saves a request and keeps your quota.
- They are invisible to people and need no outside service.
- Signing the stamp with the Django secret key needs no database row and no cache entry.

**Costs.**

- The count is kept per server process, so with two processes one visitor could post up to 20 an hour. That's still far too few to be a problem, and sharing the count would need Redis ([N4](newsletter.md#n4-spam-protection-without-a-captcha) accepted the same).
- A real person who somehow submits within 3 seconds is told "waiting for review" and the comment is lost. The comment box can't be filled in that fast by hand.
- Changing the Django `SECRET_KEY` makes stamps from open pages invalid, so those comments are thrown away. Reloading the page fixes it.

---

## M5. No email verification to post a comment

**Decision (yours).** Posting a comment doesn't require clicking a link in an email. The address is checked only for a valid format. If spam gets through later, adding verification stays possible.

**Why.**

- A one-time visitor who has to leave the page, find an email and click before the comment even enters the queue usually doesn't. Verification would cost real comments.
- It would also mean the site emails whatever address is typed into a form, which is the abuse [N3](newsletter.md#n3-a-signup-never-reveals-who-is-subscribed) and [M6](#m6-reply-alerts-double-opt-in-without-mailing-anyone-for-an-unreviewed-comment) avoid.
- It isn't needed to be safe. The address never appears on the page, Akismet filters the comments, and you review everything. The only use of the address is reply alerts, and those have their own double opt-in, so a wrong or borrowed address can't cause email.

**Why not the alternative.** Verification before the comment is queued, which is what many blog systems do, protects a queue that is already protected by [M2](#m2-every-comment-is-reviewed-before-it-shows) and [M3](#m3-akismet-checks-every-comment-first), and loses comments to do it.

**Costs.**

- Anyone can type any name and any address. A comment can claim to be from someone it isn't. You decide at review, and only the name is shown.
- You can't be sure a commenter's address works.

**When to revisit.** If spam gets past Akismet and your review often, or if someone is impersonated. The change would be to send a link right after the form is submitted, and to put the comment in the queue only after the click. The token and email code for it already exist for [M6](#m6-reply-alerts-double-opt-in-without-mailing-anyone-for-an-unreviewed-comment).

---

## M6. Reply alerts: double opt-in without mailing anyone for an unreviewed comment

**Decision.** Under the form there is a box, "Email me when someone replies". It works in three steps:

1. The box is ticked when the comment is posted. Nothing is emailed. The comment's reply alerts are "Asked for, not confirmed".
2. When you approve the comment, the site sends **one** email: "Your comment on … is live", with a button **Email me replies**.
3. Only after that click are reply alerts on. From then on, a reply to that comment sends an email with the reply and a link to it. Every one has a stop link and the one-click unsubscribe headers ([N11](newsletter.md#n11-unsubscribing-a-button-on-a-page-plus-one-click-headers) works the same way).

An alert goes only to the author of the comment that was answered, not to everyone in the thread. It is not sent:

- when the replier and the commenter have the same address,
- for a comment you wrote yourself,
- for a reply that isn't approved yet,
- when the commenter hasn't clicked the confirm link yet.

The confirm email is sent when the comment is approved, in the admin request. If it can't be sent, the comment is still approved, the admin shows a warning, and that commenter simply has no alerts.

**Why.**

- Someone can type another person's address and tick the box. If the site emailed at posting time, a spammer could make it send mail to strangers. Here nothing is sent for a comment you haven't approved, and spam is never approved, so a spammer typing a victim's address causes no email at all.
- Nobody can reply to a comment before it is live, so waiting for approval loses nothing.
- Clicking the link proves that the owner of the address wants the alerts, which is the whole point of double opt-in ([N1](newsletter.md#n1-double-opt-in)).
- Reply alerts keep conversations going. A reader who asks a question gets the answer.

**Why not the alternatives.**

- **Email a confirmation straight after posting.** It's the usual way, but it makes the site mail strangers because of an unreviewed comment.
- **Email every reply to whoever ticked the box, with no confirmation.** Anyone could sign up someone else, and each reply would then mail them.
- **No reply alerts.** Questions would go unanswered, because readers don't come back to look.

**Costs.**

- A reply approved before the commenter has clicked the confirm link sends no alert. That includes your own reply to a comment that was still waiting: replying approves it, and the commenter gets the confirm email, not the alert. They see the reply when they come back.
- A commenter who ticks the box gets up to two kinds of email, the confirm email once and then the alerts.
- If the mail server is down at the moment you approve, that commenter never gets the confirm email.

**Details.** The confirm and stop links use a random token stored on the comment, like [N2](newsletter.md#n2-one-random-token-per-subscriber-stored-in-the-database), so old links keep working. Confirming happens when the page opens, as in [N12](newsletter.md#n12-confirming-happens-when-the-link-opens). Stopping needs a button press, as in [N11](newsletter.md#n11-unsubscribing-a-button-on-a-page-plus-one-click-headers). The emails are built with the same code as the newsletter's ([`core/emails.py`](../../backend/core/emails.py)) and sent straight away, not through the worker's queue: a few emails at a time don't need one.

---

## M7. No email to you about new comments

**Decision (yours).** The site never emails you about a new comment. The admin shows how many are waiting: in the Comments menu entry (`Comments (3)`) and on the admin home page ("3 comments waiting for review").

**Why.**

- One email path fewer to set up, to break and to keep out of spam folders.
- No inbox noise, and nobody can flood your inbox by posting comments in bulk.
- You open the admin to write posts anyway, and the count is the first thing you see.

**Cost.** You find out only when you open the admin. A comment can wait.

**When to revisit.** If comments sit unreviewed for days. A daily summary from the worker, sent only when something is waiting, would fit without new infrastructure.

---

## M8. Only your heart, no public likes

**Decision (yours).** The only "like" is yours. You can heart an approved comment in the admin, and the site shows a badge: a heart and the text "Liked by Prabuddh". You can change the text under **Settings → Comments**. There are no public like buttons and no counts.

**Why.**

- A heart from the author is what readers care about: it says "I read this and liked it".
- Public likes need protection against repeat votes (cookies, accounts or IP checks) and a counter that changes on every click. That's the kind of write on every page view that [D1](data-and-configuration.md#d1-sqlite-as-the-database) says to avoid, and it's a new thing for bots to attack.
- Yours is one yes-or-no field on a comment.

**Why not the alternative.** Reader likes and counts add features that look like a social network, on a blog where most comments get few replies. They also invite fake counts.

---

## M9. Moderating happens only in the Wagtail admin

**Decision (yours).** Approving, marking as spam, liking and replying as the author all happen in the Wagtail admin. The public site never knows who is logged in: no "moderate" buttons for you, no author tools, no session check on a public page.

**Why.**

- The admin already has logins, permissions, messages and a good list screen. Nothing about moderation needs to be built twice.
- Public pages are rendered for everybody the same way. Because they never look at who you are, a flaw in how a comment is displayed can never act with your rights, even though the admin and the site share one domain ([A2](architecture.md#a2-one-domain-split-by-path)).

**Why not the alternatives.**

- **Moderation buttons on the public page when you are logged in.** It puts admin powers next to text written by strangers.
- **Approve and spam links in an email to you.** It conflicts with [M7](#m7-no-email-to-you-about-new-comments), and mail scanners open every link, so one could approve a comment by itself ([N11](newsletter.md#n11-unsubscribing-a-button-on-a-page-plus-one-click-headers)).

**Cost.** Replying means going to the admin. You can't reply from the post's page.

**Author replies.** The admin's **Reply** page publishes your reply at once, as the author. It is shown with an "Author" badge and your name from **Settings → Author Settings**. If the comment you answer is still waiting, publishing your reply also approves it.

---

## M10. Every moderation action goes through one module

**Decision.** Approving, marking as spam, liking and replying are plain functions in `comments/moderation.py`. The row buttons, the bulk actions and the reply page all call them. A comment's status can't be changed in its edit form: the form has only the name, the text and the heart.

**Why.** Each action has side effects: telling Akismet, and sending the reply-alert emails ([M6](#m6-reply-alerts-double-opt-in-without-mailing-anyone-for-an-unreviewed-comment)). If the status could be edited directly, or if each screen had its own code, some route would skip them. The only way to approve is now a path that does everything.

**Rules that follow.**

- Approving a comment that is already approved does nothing, so double clicks and repeated bulk actions send nothing twice.
- A failed email never undoes an action. It is logged, and shown to you as a warning.
- An action connects to the mail server only when it sends an email, and all the emails of one action share the connection. Liking, unliking and most approvals send none.
- Once the mail server can't be reached, or Akismet fails, the rest of that action doesn't try it again. Every try could wait for the whole timeout, and a bulk action would run past the server's time limit for a request. The comments themselves are still approved or marked; you get a warning for each email that wasn't sent.
- Bulk Approve and Mark as spam save each comment on its own, not inside the one database transaction Wagtail wraps around a bulk action. SQLite allows one writer at a time ([D1](data-and-configuration.md#d1-sqlite-as-the-database)), and a transaction that waits for a slow mail server or Akismet would hold back everything else that writes, such as a reader posting a comment or the worker.
- A comment marked as spam can't be replied to. Approve it first.

---

## M11. Replies are threaded one level deep

**Decision.** A top-level comment has its replies listed under it, oldest first, indented once. A reply to a reply stays in the same list and says "Replying to Name". Each comment stores the top of its thread (its `root`).

**Why.**

- Deeper indentation runs out of space on a phone, and long threads become a staircase.
- One list per thread keeps the page layout simple and the read to the database small: one query, however many replies.
- "Replying to Name" keeps the context that deeper nesting would show.

**Why not the alternatives.** A flat list loses who is answering whom. Unlimited nesting is the version that breaks on narrow screens.

**Rule.** A reply is only shown if every comment above it is shown. Hiding or deleting a comment hides what was said under it. Deleting a comment deletes its replies, and the admin's confirmation says so.

---

## M12. Plain text only, with links added by the page

**Decision.** A comment is plain text. Line breaks are kept, and the page turns `http://` and `https://` addresses into links (`rel="nofollow ugc noopener"`). It builds those links from pieces of text, never by inserting HTML. In the emails the reply text is escaped and cut at 1,000 characters.

**Why.**

- HTML written by strangers never reaches a page, so [C13](frontend.md#c13-only-rich-text-from-the-cms-is-inserted-as-html) stays true: the only HTML inserted is rich text you wrote.
- `nofollow ugc` tells search engines that you don't vouch for a link, which takes away most of the reason to post spam links.

**Why not the alternative.** Markdown or rich text needs a renderer and a sanitiser on the site, and again for emails, with a stream of security fixes to follow. A plain comment box covers what readers write on a blog.

**Cost.** No bold, no code blocks, no images.

---

## M13. Visitor details are kept for 30 days at most

**Decision.**

- **What.** With Akismet on, a comment also stores the visitor's IP address, browser string and referrer. They are kept only so that you can report a comment to Akismet later. Without Akismet nothing of the kind is stored.
- **How long.** The details of a reviewed comment are cleared 30 days after the review. A comment you marked as spam is deleted 30 days after you marked it, so a mistake can be rescued for a month, however old the comment. Spam Akismet caught, which nobody reviewed, is deleted 30 days after it was posted.
- **Who does it.** The newsletter worker runs the cleanup about once an hour and logs the counts when something was removed. `manage.py comments_cleanup` runs it once by hand.

The commenter's email stays with the comment until it is deleted, because reply alerts need it.

**Why.**

- Less personal data kept means less to protect, and less to explain in a privacy text.
- Akismet needs the IP address to learn from a report, and a report is only useful soon after the decision.
- The worker is already the site's one background process. A second container, or a cron job set up outside the repository ([N6](newsletter.md#n6-a-database-queue-and-a-small-worker-process)), for one cheap query an hour isn't worth it.

**Costs.**

- After 30 days a comment can't be reported to Akismet.
- If the worker isn't running, cleanup waits. Nothing is lost, and the details are kept longer.
- A problem in the cleanup is logged and doesn't stop the worker from sending the queue.
- The throttle keeps the IP address in memory for an hour, and nothing in the database.

---

## M14. It works without JavaScript

**Decision.** The comment form is a real HTML form that posts to the backend. With JavaScript (the normal case) it's sent in the background and the result shows in place. Without it, the backend answers with a redirect back to the post, `…?comment=pending#comment-form`, and the page shows the outcome. The **Reply** link on each comment goes to `?replyto=<id>#comment-form`, which turns the bottom form into a reply. The confirm and stop pages for reply alerts are plain pages too.

**Why.** The same reasons as [N13](newsletter.md#n13-it-works-without-javascript): a few lines for readers who block scripts, and the same endpoint for both.

**Cost.** After a mistake (say, no email) a reader without JavaScript has to type the comment again, because the page can't carry it back.

---

## M15. Comments can be switched off everywhere or on one post

**Decision.** Two switches:

- **Settings → Comments → Enabled** turns comments off on every post. The thread and the form disappear. Nothing is deleted, and turning it back on restores them.
- **Allow comments**, in the post's **Settings** tab under **Comments**, closes one post. Comments already on it stay visible, and the form is replaced by "Comments are closed."

**Why.** The two cases are different: a wave of spam or a holiday (stop everywhere with one click), and a post that attracts trouble (close only that one). Neither deletes anything.

**Cost.** A closed post still shows its old comments. To hide them, mark them as spam or delete them.

---

## M16. The site runs without Akismet configured

**Decision.** With `AKISMET_API_KEY` empty, no request to Akismet is made. Every comment goes to review as "Not checked", and no visitor details are stored. `manage.py check --deploy` warns (`comments.W001`) until the key is set.

**Why.** The same idea as [N17](newsletter.md#n17-the-site-runs-without-email-configured): deploying the comments code can't take the site down, and local development needs no account. The warning makes the gap visible without making it fatal.

**Cost.** Without the key, all the spam arrives in your queue by hand. Set the key before the site gets traffic ([`comments.md`](../comments.md#get-an-akismet-key)).

---

## M17. The admin side

**Decision.** A **Comments** menu entry, built as a Wagtail snippet:

- **The list** shows waiting comments first, then the newest. Columns: the start of the comment, name, email, post, status, Akismet verdict, liked and date. Filters: status, Akismet verdict and post. Search: name, email and text.
- **Row buttons.** Waiting comments get **Approve** and **Mark as spam** buttons in their row. Every comment has a **More** menu with the other actions that apply to it: **Approve**, **Mark as spam**, **Reply** (not for spam), **Like** or **Remove your like** (approved only), **Edit** and **Delete**.
- **Bulk actions:** Approve, Mark as spam and Delete, each with a confirmation. The Delete confirmation says that replies go too.
- **The edit page** shows the details read-only (post, status, verdict, email, reply alerts, date, the comment it answers), and lets you change only the name, the text and the heart.
- **The reply page** at `/admin/comments/<id>/reply/` ([M9](#m9-moderating-happens-only-in-the-wagtail-admin)).
- **The count** of waiting comments in the menu and on the admin home page ([M7](#m7-no-email-to-you-about-new-comments)).
- **Permissions.** Approving, spam, liking and replying need "Can change comment". Deleting needs "Can delete comment". Superusers have both. Nobody can "add" a comment by hand: comments come from readers or from the reply page.

Wagtail's own editor comments on drafts (`WAGTAILADMIN_COMMENTS_ENABLED`) are switched off. With one author they aren't needed, and they would be confused with readers' comments.

**Why.**

- A snippet comes with the list, filters, search, edit and delete pages and bulk actions, so almost nothing is built from scratch.
- Pending comments first, and buttons right in the row, make the common job (go through the queue) quick.
- Showing the details read-only lets you see what Akismet and the commenter did without being able to edit it.

**Why not the alternatives.** A custom admin section would be more code to write and maintain. Django's own admin isn't installed and has a separate look and login. Wagtail's plain model viewset has no bulk actions.

**Cost.** The row buttons, the bulk-action base class and the count use some parts of Wagtail that aren't a documented extension point. After a Wagtail upgrade, check the Comments menu (the tests cover it).

---

## M18. What was left out on purpose

**Decision.** These common comment features were not built:

| Left out | Why |
|---|---|
| Gravatar pictures | Each commenter's picture is a request to a third party, and it exposes a hash of their email |
| A website field | It attracts spam links, and it would give spammers a reason to post |
| Reader accounts | Passwords, resets and data to protect, for a blog that gets a few comments |
| Editing or deleting your own comment | It needs proof of who you are, and the address isn't verified ([M5](#m5-no-email-verification-to-post-a-comment)). You can edit or delete any comment in the admin |
| Public likes and counts | See [M8](#m8-only-your-heart-no-public-likes) |
| Email to you about new comments | See [M7](#m7-no-email-to-you-about-new-comments) |
| Email verification | See [M5](#m5-no-email-verification-to-post-a-comment) |
| Paging the comments | A post loads all its approved comments in one request. Fine for hundreds |
| A comments RSS feed, comment search | Nobody asked for them |

**When to revisit.** Paging is the first one to add if a post ever gets more than a few hundred comments. The others, only if you miss them.
