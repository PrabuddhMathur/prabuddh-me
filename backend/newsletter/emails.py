"""
The newsletter's two emails: the signup confirmation and a post. Each is a plain-text
body with an HTML alternative. Links are absolute, built from settings.FRONTEND_URL.
"""

from urllib.parse import quote

from django.conf import settings

from core.emails import build_email, frontend_url, html_of, site_name

# html_of and site_name are re-exported for the admin views and the tests.
__all__ = ["build_confirmation", "build_issue", "html_of", "send_confirmation", "site_name"]

# Stands in for a subscriber's token in test sends, so no real link is exposed.
TEST_TOKEN = "test"


def confirm_url(subscriber):
    return frontend_url(f"/newsletter/confirm/?token={quote(subscriber.token)}")


def unsubscribe_page_url(token):
    return frontend_url(f"/newsletter/unsubscribe/?token={quote(token)}")


def unsubscribe_api_url(token):
    return frontend_url(f"/api/v2/newsletter/unsubscribe/?token={quote(token)}")


def build_confirmation(subscriber):
    name = site_name()
    return build_email(
        f"Confirm your subscription to {name}",
        "newsletter/emails/confirm",
        {"confirm_url": confirm_url(subscriber)},
        to=[subscriber.email],
    )


def send_confirmation(subscriber):
    """Sends the confirmation email now. Raises if the mail server refuses it."""
    build_confirmation(subscriber).send()


def _image_url(post):
    """(absolute URL, alt text) of the featured image as a 1200x630 crop, or (None, "")."""
    image = post.featured_image
    if image is None:
        return None, ""
    try:
        url = image.get_rendition("fill-1200x630").url
    except Exception:  # A missing or unreadable file must not stop the whole send.
        return None, ""
    if not url.startswith(("http://", "https://")):
        url = frontend_url(url)
    return url, image.title


def build_issue(post, subscriber=None, *, to=None, test=False, connection=None):
    """
    The email for a post. Pass the subscriber for a real send; a test send passes
    `to` (an address) instead and gets a placeholder unsubscribe link.
    """
    token = TEST_TOKEN if subscriber is None else subscriber.token
    if to is None:
        to = [subscriber.email]
    image_url, image_alt = _image_url(post)
    subject = post.title
    headers = {
        "List-Unsubscribe": f"<{unsubscribe_api_url(token)}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }
    if settings.NEWSLETTER_REPLY_TO:
        headers["Reply-To"] = settings.NEWSLETTER_REPLY_TO
    context = {
        "post": post,
        "post_url": frontend_url(post.get_date_url()),
        "image_url": image_url,
        "image_alt": image_alt,
        "unsubscribe_url": unsubscribe_page_url(token),
    }
    return build_email(
        f"[Test] {subject}" if test else subject,
        "newsletter/emails/post",
        context,
        headers=headers,
        to=to,
        connection=connection,
    )
