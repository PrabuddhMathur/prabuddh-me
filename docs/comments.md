# Comments: set them up and run them

This guide covers what you do to get comments working on the live site (get a spam filter key, turn it on), and how to look after them day to day. To try comments on your own machine first, see [`local-development.md`](local-development.md#try-the-comments-locally). For why they work this way, see the [design decisions](decisions/comments.md).

Provider facts (plans, prices, privacy) were checked against Akismet's own pages in **October 2026**. They change. If something doesn't match, trust Akismet's page, and update this file.

## How it works

1. A reader writes a name, an email address and a comment under a post. There are no accounts. The email is never shown.
2. The backend asks **Akismet**, a spam-filtering service, whether the comment is spam.
3. Every comment, whatever Akismet says, waits for you. Only comments you **approve** in the Wagtail admin appear on the site. Akismet's spam goes to the **Spam** list.
4. Readers can reply to comments (replies are threaded). You can **like** a comment, which shows a badge ("Liked by Prabuddh"), and **reply as the author**, both from the admin.
5. A reader can tick "Email me when someone replies". When you approve that comment, the site sends them **one** email with a button to confirm. Only after they click it do they get an email when someone replies.

You are never emailed about new comments. The admin shows how many are waiting: in the **Comments** menu entry, and on the admin home page.

Without an Akismet key the site still works: every comment goes to review unchecked, and you do all the filtering yourself. That's fine for trying things, and not for a live site.

## Get an Akismet key

Akismet's **Personal plan** is free for personal, non-commercial sites. It's a "pay what you can" plan: set the slider to **$0**. Akismet counts a site as commercial, and needing a paid plan, if it has ads or affiliate links, sells products or services, asks for donations or sponsorships, or is related to a business, nonprofit or school ([Akismet: free or paid](https://akismet.com/support/getting-started/free-or-paid/)). If the blog ever gets any of those, switch plans.

1. Open <https://akismet.com/pricing/>, choose the **Personal** plan, set the price to $0 and finish signing up.
2. Akismet emails you the **API key**, a short string of letters and numbers ([Akismet: API key](https://akismet.com/support/getting-started/api-key/)). If you lose it, it can be sent again from <https://akismet.com/resend>.
3. Treat the key like a password. Don't put it in git or in a chat.

## Turn it on

1. On the server, open `backend/.env` and add:

   ```sh
   AKISMET_API_KEY=your-key-here
   ```

   `FRONTEND_URL` must already be there (`https://prabuddh.in`). It's the site address that Akismet is told. Comments don't need any other setting.

2. Restart the backend so it reads the file again (the worker doesn't use the key):

   ```sh
   docker compose -f docker-compose.prod.yaml up -d --force-recreate backend
   ```

3. Run the production checklist. The Akismet warning must be gone:

   ```sh
   docker compose -f docker-compose.prod.yaml exec backend python manage.py check --deploy
   ```

   If it says `comments.W001 Akismet isn't configured`, `AKISMET_API_KEY` is empty or the container hasn't been restarted. (The two `security.W005`/`W021` warnings about HSTS were already there.)

Reply alerts need email. They use the same `EMAIL_*` settings as the newsletter: see [`newsletter-production.md`](newsletter-production.md#2-put-the-settings-in-backendenv). Without them the comments work, but approving a comment whose author asked for alerts shows a warning, and no email goes out.

## Try it before you trust it

Akismet has a test mode. With it on, every request carries a "this is a test" flag, and Akismet doesn't learn from your comments, so you can try things without teaching it wrong answers.

1. Add `AKISMET_TEST_MODE=True` to `backend/.env` and recreate the backend as above.
2. Post a normal comment on a post. In **Comments**, its **Akismet** column usually says **Not spam**.
3. Post a comment with the email address `akismet-guaranteed-spam@example.com` ([Akismet: comment-check](https://akismet.com/developers/comment-check/)). Akismet always calls it spam. It appears with the status **Spam** and verdict **Spam**, and nothing shows on the site.
4. Remove `AKISMET_TEST_MODE` (or set it to `False`) and recreate the backend again. Test mode on a live site would stop Akismet from ever learning.

If a verdict says **Not checked**, Akismet wasn't asked or didn't answer: see [Troubleshooting](#troubleshooting).

## Day to day

Open **Comments** in the admin menu. A number in brackets shows how many are waiting, `Comments (3)`. The same count is on the admin home page ("3 comments waiting for review"), and clicking it opens the waiting list.

### The list

- Waiting comments come first, then the newest.
- Columns: the start of the comment (it opens the comment), name, email, post, status, Akismet verdict, a tick if you liked it, and the date.
- Use the filters on the side (status, Akismet verdict, post) and the search box (name, email and text).
- Statuses: **Waiting for review**, **Approved**, **Spam**. Only approved comments are public.

### What you can do to a comment

| Action | Where | What it does |
|---|---|---|
| **Approve** | Row button, **More** menu, bulk | Makes it public. Sends the reply-alert confirmation email if the commenter asked for alerts. If it was spam, tells Akismet it was a mistake |
| **Mark as spam** | Row button, **More** menu, bulk | Hides it. Tells Akismet, unless Akismet had already called it spam |
| **Reply** | **More** menu | Opens the reply page: see [Replying](#replying) |
| **Like** / **Remove your like** | **More** menu | Shows or hides your heart badge. Only for approved comments |
| **Edit** | Click the comment | Change the name or text, or the heart. The status can't be changed here, only with the actions above |
| **Delete** | **More** menu, bulk | Deletes it for good. **Replies to it are deleted too** |

To act on several at once, tick the boxes in the list and use the actions at the bottom. Each asks you to confirm and shows what it will do. A message tells you the result, for example "Approved 3 comments."

The edit page also shows, read-only: the post (a link to the comment on the live site), the status, Akismet's verdict, the email, whether reply alerts are on, when it was posted and, for a reply, the comment it answers.

A comment marked as spam can't be replied to. Approve it first.

### Replying

**Reply** (in the **More** menu) opens a page that shows the comment, a box for your reply and **Publish reply**. Your reply appears on the site at once, with an **Author** badge and your name from **Settings → Author Settings**. If the comment was still waiting, publishing your reply **approves it too**, and the page says so.

Replying happens only in the admin. The site itself never knows you are logged in.

### Reply alerts

These are the emails to readers who ticked "Email me when someone replies".

- When you approve their comment, they get one email: "Your comment on … is live", with a button **Email me replies**. Until they click it, they get nothing more.
- After the click, each reply to their comment (yours, or another reader's, once approved) sends them an email with the reply and a link. Every one has a **Stop these emails** link.
- A reply that is approved before they have clicked doesn't send an alert, and neither does your reply to a comment that was still waiting (replying approves it, and the confirmation email goes out instead).
- Nobody is emailed when they reply to their own comment, and you never get these emails for your own comments.
- If an email can't be sent, the comment is still approved, and the admin shows a warning with the reason (for example a wrong mail password). That reader just won't get alerts.

### Changing the "Liked by" text

**Settings → Comments → Like label.** The default is "Liked by Prabuddh". Save, and the badge changes on every liked comment.

### Turning comments off

- **On one post:** open the post, go to the **Settings** tab, find **Comments**, untick **Allow comments**, and publish. Existing comments stay visible, and the form is replaced by "Comments are closed."
- **Everywhere:** **Settings → Comments**, untick **Enabled**. The comments and the form disappear from every post. Nothing is deleted, and ticking it again brings them back.

## What is stored, and for how long

| What | Kept | Why |
|---|---|---|
| Name, email, text, the post, the dates | Until you delete the comment | The comment itself. The email is used only for reply alerts and is never shown |
| IP address, browser and referrer | Until 30 days after you reviewed the comment, then cleared. Stored only when Akismet is on | Only to report a comment to Akismet |
| Comments marked as spam | Deleted 30 days after you marked them; spam Akismet caught on its own, 30 days after it was posted | So you can rescue a mistake first |
| A random token per comment | As long as the comment | For its confirm and stop links |

The cleanup runs by itself about once an hour, inside the newsletter worker (the `worker` container). To run it once by hand:

```sh
docker compose -f docker-compose.prod.yaml exec backend python manage.py comments_cleanup
```

**What Akismet receives** with every comment: the name, email, text, IP address, browser, the referrer, and the post's address. Akismet says it keeps most spam-related data for between two weeks and ninety days ([Akismet: privacy](https://akismet.com/privacy/)). The comment form tells readers this and links to that page.

**Privacy text.** Say on your site that comments are checked by Akismet, that email addresses are kept to send reply emails if asked and are never shown, and how a reader can ask you to remove a comment.

**Deleting someone's data.** Open **Comments**, search for their email address, tick their comments and use **Delete**.

**Backups.** Comments live in the SQLite database, in the `backend_data` volume. See "Backups" under [Day to day](newsletter-production.md#day-to-day) in the newsletter guide.

## Settings you can change

All in `backend/.env`; recreate `backend` after editing.

| Variable | Meaning |
|---|---|
| `AKISMET_API_KEY` | Your Akismet key. Empty means Akismet is off. |
| `AKISMET_TEST_MODE` | Optional. `True` marks every Akismet request as a test. Default `False`. |
| `COMMENTS_POST_LIMIT` | Optional. Comments per visitor address per hour. Default 10. |
| `FRONTEND_URL` | The site address. Used for the links in emails and as the address Akismet is told. |

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Every comment says **Not checked** | Akismet wasn't asked, or didn't answer. Check `AKISMET_API_KEY` in `backend/.env` and that the backend was recreated. Then look at the backend logs: `docker compose -f docker-compose.prod.yaml logs --tail 50 backend`. A line starting "Akismet check failed" gives the reason. A wrong key shows up there too. |
| `comments.W001` in `check --deploy` | `AKISMET_API_KEY` is empty. |
| Real comments land in **Spam** | Akismet makes mistakes. Open the comment and **Approve** it: that also tells Akismet. Don't leave them, or it keeps making the same mistake. |
| Spam gets into **Waiting for review** | Mark it as spam. That teaches Akismet. A lot of it means the key is missing or not working: see the first row. |
| A reader says their comment never appeared | It was waiting, or it was caught as spam (check the **Spam** filter, search their name). A comment posted within 3 seconds of the page loading, or with the hidden `website` field filled in, is thrown away without a record. Comments over the hourly limit get "Too many comments" instead. |
| "Too many comments from your connection" | One address posted more than `COMMENTS_POST_LIMIT` comments in an hour. Wait, or raise the limit. |
| A warning "The email to … couldn't be sent" after approving | The mail settings are wrong or the server is down. Run `sendtestemail` ([newsletter guide, step 4](newsletter-production.md#4-test-the-email-connection)). The comment was still approved, but that reader won't get reply alerts. |
| Links in the emails point to `localhost` or the wrong site | `FRONTEND_URL` is missing or wrong in `backend/.env`. Fix it and recreate `backend` and `worker`. |
| Comments don't show on a post | **Settings → Comments → Enabled** is off, or no comment on that post is approved yet. A post's **Allow comments** only stops new comments; old ones stay visible. |
| The **Comments** menu is missing | Your user lacks "Can change comment" and "Can delete comment" (give them in **Settings → Groups**). Superusers always have them. |
| Spam isn't deleted after 30 days | The worker isn't running: `docker compose -f docker-compose.prod.yaml ps worker`. Or run `comments_cleanup` by hand. |
| Edited `backend/.env` but nothing changed | The container reads it when it starts. Recreate it: `docker compose -f docker-compose.prod.yaml up -d --force-recreate backend`. |
