"""
Akismet, the spam filter: checks a comment when it is posted and learns from the owner's
decisions. Without AKISMET_API_KEY none of this does anything and no request is made.

A problem with Akismet (down, slow, a wrong key) must never block or lose a comment, so
every error is logged and the comment goes to review as "unchecked".
"""

import logging
from contextlib import contextmanager
from datetime import UTC, datetime

import akismet
import httpx
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address

from core.emails import frontend_url
from core.form_posts import client_ip

logger = logging.getLogger(__name__)

# Seconds. A comment waits for Akismet's answer, so don't let it wait long.
HTTP_TIMEOUT = 4.0
# The name of the form field that only bots fill in (see views.py). Akismet is told
# about it so it can treat a filled-in one as spam.
HONEYPOT_FIELD = "website"
MAX_DETAIL_LENGTH = 500

# What check() answers.
DISCARD = "discard"
SPAM = "spam"
HAM = "ham"
UNCHECKED = "unchecked"

_VERDICTS = {
    akismet.CheckResponse.HAM: HAM,
    akismet.CheckResponse.SPAM: SPAM,
    akismet.CheckResponse.DISCARD: DISCARD,
}


def is_configured():
    return bool(settings.AKISMET_API_KEY)


@contextmanager
def client():
    """
    An Akismet client with explicit settings (not the PYTHON_AKISMET_* variables) that
    doesn't check the key on every use: a wrong key shows up as an error on the first
    comment, which is logged.
    """
    http = httpx.Client(headers={"User-Agent": akismet.USER_AGENT}, timeout=HTTP_TIMEOUT)
    try:
        config = akismet.Config(key=settings.AKISMET_API_KEY, url=settings.FRONTEND_URL)
        yield akismet.SyncClient(config=config, http_client=http)
    finally:
        http.close()


def request_details(request):
    """The visitor's IP address, browser and referrer, as stored on a comment for reports."""
    ip = client_ip(request)
    try:
        validate_ipv46_address(ip)
    except ValidationError:
        ip = None
    return {
        "ip_address": ip,
        "user_agent": request.headers.get("User-Agent", "")[:MAX_DETAIL_LENGTH],
        "referrer": request.headers.get("Referer", "")[:MAX_DETAIL_LENGTH],
    }


def _arguments(comment, post, *, date, user_agent, referrer):
    """What Akismet is told about a comment (the same for checks and reports)."""
    arguments = {
        "user_agent": user_agent,
        "referrer": referrer,
        "permalink": frontend_url(post.get_date_url()),
        "comment_type": "reply" if comment.parent_id else "comment",
        "comment_author": comment.name,
        "comment_author_email": comment.email,
        "comment_content": comment.body,
        "comment_date_gmt": date.astimezone(UTC).isoformat(),
        "blog_lang": "en",
        "blog_charset": "UTF-8",
        "honeypot_field_name": HONEYPOT_FIELD,
    }
    if post.last_published_at:
        arguments["comment_post_modified_gmt"] = post.last_published_at.astimezone(UTC).isoformat()
    if settings.AKISMET_TEST_MODE:
        arguments["is_test"] = 1
    return arguments


def check(comment, request, post):
    """
    Asks Akismet about a comment that is about to be saved. Returns "discard" (blatant
    spam: don't even store it), "spam", "ham" (not spam) or "unchecked".
    """
    if not is_configured():
        return UNCHECKED
    details = request_details(request)
    if not details["ip_address"]:
        return UNCHECKED
    arguments = _arguments(
        comment,
        post,
        date=datetime.now(UTC),
        user_agent=details["user_agent"],
        referrer=details["referrer"],
    )
    try:
        with client() as akismet_client:
            response = akismet_client.comment_check(user_ip=details["ip_address"], **arguments)
    except Exception as exc:  # The library's errors, the network's, anything.
        logger.warning(
            "Akismet check failed, the comment goes to review: %s: %s", type(exc).__name__, exc
        )
        return UNCHECKED
    return _VERDICTS[response]


def _report(method, comment):
    if not is_configured() or not comment.ip_address:
        return None
    arguments = _arguments(
        comment,
        comment.post,
        date=comment.created_at,
        user_agent=comment.user_agent,
        referrer=comment.referrer,
    )
    try:
        with client() as akismet_client:
            getattr(akismet_client, method)(user_ip=comment.ip_address, **arguments)
    except Exception as exc:
        logger.warning("Akismet %s failed: %s: %s", method, type(exc).__name__, exc)
        return False
    return True


def report_spam(comment):
    """
    Tells Akismet a comment that got through is spam. True when it was sent, False when
    that failed, None when there was nothing to send (no key, or no visitor details).
    """
    return _report("submit_spam", comment)


def report_ham(comment):
    """Tells Akismet a comment it called spam is fine. Answers like report_spam()."""
    return _report("submit_ham", comment)
