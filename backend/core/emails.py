"""
What the site's emails (the newsletter's, the comments') have in common: absolute links
to the public site, the shared HTML layout (templates/core/emails/base.html) and one
way to build a message from a plain-text template plus an HTML one.
"""

from email.utils import make_msgid
from urllib.parse import urlsplit

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from wagtail.models import Site

from .models import SiteSettings

# The site's light-theme primary colour and its text colour (frontend/app/assets/css/main.css),
# as hex because email clients don't read oklch().
BUTTON_COLOR = "#000000"
BUTTON_TEXT_COLOR = "#e0e7ff"


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


def build_email(subject, template, context, *, to, headers=None, connection=None):
    """
    A message with a plain-text body and an HTML alternative, from the templates
    `<template>.txt` and `<template>.html` (a full template path without the extension,
    such as "newsletter/emails/post"). Nothing is sent: call .send() on the result.
    """
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
        body=render_to_string(f"{template}.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        headers=headers,
        connection=connection,
    )
    message.attach_alternative(render_to_string(f"{template}.html", context), "text/html")
    return message


def html_of(message):
    """The HTML alternative of a message built here."""
    return next(content for content, mimetype in message.alternatives if mimetype == "text/html")
