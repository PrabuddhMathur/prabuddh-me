"""
The comments' two emails, both only for readers who asked for reply alerts:

- when their comment goes live, one email to confirm that they want the alerts (so nobody
  gets email because a stranger typed their address into a form);
- when someone replies to a comment whose author confirmed, a reply alert.

Each is a plain-text body with an HTML alternative. Links are absolute, built from
settings.FRONTEND_URL.
"""

from urllib.parse import quote

from core.emails import build_email, frontend_url

# A long reply is cut here; the email links to the whole of it.
REPLY_EXCERPT_LENGTH = 1000


def confirm_url(comment):
    return frontend_url(f"/comments/alerts/confirm/?token={quote(comment.token)}")


def stop_page_url(token):
    return frontend_url(f"/comments/alerts/stop/?token={quote(token)}")


def stop_api_url(token):
    return frontend_url(f"/api/v2/comments/alerts/stop/?token={quote(token)}")


def build_alerts_confirmation(comment, connection=None):
    """To a commenter whose comment is live and who asked for reply alerts."""
    post = comment.post
    return build_email(
        f"Your comment on “{post.title}” is live",
        "comments/emails/alerts_confirm",
        {
            "post": post,
            "comment_url": comment.public_url(),
            "confirm_url": confirm_url(comment),
        },
        to=[comment.email],
        connection=connection,
    )


def build_reply_alert(reply, connection=None):
    """To the author of the comment `reply` answers."""
    parent = reply.parent
    post = reply.post
    excerpt = reply.body
    if len(excerpt) > REPLY_EXCERPT_LENGTH:
        excerpt = excerpt[:REPLY_EXCERPT_LENGTH].rstrip() + "…"
    return build_email(
        f"{reply.name} replied to your comment on “{post.title}”",
        "comments/emails/reply",
        {
            "post": post,
            "reply": reply,
            "reply_excerpt": excerpt,
            "reply_url": reply.public_url(),
            "stop_url": stop_page_url(parent.token),
        },
        to=[parent.email],
        headers={
            "List-Unsubscribe": f"<{stop_api_url(parent.token)}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
        connection=connection,
    )
