"""
The newsletter's two emails: the signup confirmation and a post. Each is a plain-text
body with an HTML alternative. Links are absolute, built from settings.FRONTEND_URL.
"""

from email.utils import make_msgid
from urllib.parse import quote, urlsplit

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from wagtail.models import Site

from core.models import SiteSettings

# The site's light-theme primary colour and its text colour (frontend/app/assets/css/main.css),
# as hex because email clients don't read oklch().
BUTTON_COLOR = "#000000"
BUTTON_TEXT_COLOR = "#e0e7ff"

# Stands in for a subscriber's token in test sends, so no real link is exposed.
TEST_TOKEN = "test"


def frontend_url(path=""):
    """An absolute link to the public site."""
    return settings.FRONTEND_URL.rstrip("/") + path


def site_name():
    """The site name from the admin's site settings, or the default one."""
    site = Site.objects.filter(is_default_site=True).first()
    if site is not None:
        name = SiteSettings.for_site(site).site_name
        if name:
            return name
    return settings.WAGTAIL_SITE_NAME


def one_line(text):
    """Header values must not contain line breaks."""
    return " ".join(str(text).split())


def confirm_url(subscriber):
    return frontend_url(f"/newsletter/confirm/?token={quote(subscriber.token)}")


def unsubscribe_page_url(token):
    return frontend_url(f"/newsletter/unsubscribe/?token={quote(token)}")


def unsubscribe_api_url(token):
    return frontend_url(f"/api/v2/newsletter/unsubscribe/?token={quote(token)}")


def _build(subject, template, context, headers=None, to=None, connection=None):
    context = {
        "site_name": site_name(),
        "site_url": frontend_url("/"),
        "site_host": urlsplit(settings.FRONTEND_URL).netloc,
        "button_color": BUTTON_COLOR,
        "button_text_color": BUTTON_TEXT_COLOR,
        "subject": subject,
        **context,
    }
    headers = {
        # On the site's domain. Django would use this machine's name, which in Docker is a
        # container ID, and spam filters count a Message-ID without a real domain against it.
        "Message-ID": make_msgid(domain=urlsplit(settings.FRONTEND_URL).hostname),
        **(headers or {}),
    }
    message = EmailMultiAlternatives(
        subject=one_line(subject),
        body=render_to_string(f"newsletter/emails/{template}.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        headers=headers,
        connection=connection,
    )
    html = render_to_string(f"newsletter/emails/{template}.html", context)
    message.attach_alternative(html, "text/html")
    return message


def build_confirmation(subscriber):
    name = site_name()
    return _build(
        f"Confirm your subscription to {name}",
        "confirm",
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
    return _build(
        f"[Test] {subject}" if test else subject,
        "post",
        context,
        headers=headers,
        to=to,
        connection=connection,
    )


def html_of(message):
    """The HTML alternative of a message built here."""
    return next(content for content, mimetype in message.alternatives if mimetype == "text/html")
