"""
The public newsletter API (see config/urls.py): subscribe, confirm and unsubscribe.

The Nuxt frontend sends JSON. Plain HTML form posts also work, for visitors without
JavaScript: they get a 303 redirect to a frontend page that shows the outcome.
"""

import json
import logging
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from . import emails
from .models import Subscriber

logger = logging.getLogger(__name__)

# Don't send a pending subscriber another confirmation more often than this.
RESEND_COOLDOWN = timedelta(minutes=10)
THROTTLE_WINDOW = 60 * 60  # seconds
MAX_EMAIL_LENGTH = 254

JSON_STATUS_CODES = {"ok": 200, "invalid_email": 400, "rate_limited": 429, "email_failed": 503}


def _is_json(request):
    return request.content_type == "application/json"


def _read_body(request):
    """The request's fields as a dict, from a JSON body or an HTML form."""
    if _is_json(request):
        try:
            data = json.loads(request.body or b"{}")
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    return request.POST.dict()


def _text(value):
    return value if isinstance(value, str) else ""


def _client_ip(request):
    # Caddy sets X-Real-IP to the visitor's address; without a proxy fall back to the socket.
    return request.headers.get("X-Real-IP") or request.META.get("REMOTE_ADDR", "")


def _throttled(request):
    """Counts this request against the client's hourly limit. True when over it."""
    key = f"newsletter-subscribe:{_client_ip(request)}"
    cache.add(key, 0, THROTTLE_WINDOW)  # Only sets the expiry when the key is new.
    try:
        count = cache.incr(key)
    except ValueError:  # The key expired between the two calls.
        cache.set(key, 1, THROTTLE_WINDOW)
        count = 1
    return count > settings.NEWSLETTER_SUBSCRIBE_LIMIT


def _see_other(url):
    """A 303 redirect, so the browser follows a POST with a GET."""
    response = HttpResponse(status=303)
    response["Location"] = url
    return response


def _clean_email(value):
    """The normalised address, or None when it isn't a valid one."""
    email = Subscriber.normalise(_text(value))
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return None
    try:
        validate_email(email)
    except ValidationError:
        return None
    return email


def _send_confirmation(subscriber):
    """Sends the confirmation and records when. Returns "ok" or "email_failed"."""
    try:
        emails.send_confirmation(subscriber)
    except Exception:
        # The row stays as it is, so trying again sends it again.
        logger.exception("Couldn't send the newsletter confirmation email")
        return "email_failed"
    subscriber.confirmation_sent_at = timezone.now()
    subscriber.save(update_fields=["confirmation_sent_at"])
    return "ok"


def _subscribe(request):
    """Handles one signup and returns the status string."""
    if _throttled(request):
        return "rate_limited"
    data = _read_body(request)
    if _text(data.get("website")).strip():  # The honeypot: only bots fill it in.
        return "ok"
    email = _clean_email(data.get("email"))
    if email is None:
        return "invalid_email"

    subscriber, created = Subscriber.objects.get_or_create(email=email)
    if subscriber.status == Subscriber.SUBSCRIBED:
        return "ok"  # Same answer as for a new address, so nobody can probe who is subscribed.
    if subscriber.status == Subscriber.UNSUBSCRIBED:
        subscriber.status = Subscriber.PENDING
        subscriber.save()
    elif not created:
        sent_at = subscriber.confirmation_sent_at
        if sent_at and timezone.now() - sent_at < RESEND_COOLDOWN:
            return "ok"
    return _send_confirmation(subscriber)


@csrf_exempt  # Called by the public site's form; the honeypot and throttle guard it instead.
@require_POST
def subscribe(request):
    """POST /api/v2/newsletter/subscribe/ with {"email", "website"}."""
    status = _subscribe(request)
    if _is_json(request):
        return JsonResponse({"status": status}, status=JSON_STATUS_CODES[status])
    return _see_other(f"/newsletter/?{urlencode({'status': status})}")


@csrf_exempt
@require_POST
def confirm(request):
    """POST /api/v2/newsletter/confirm/ with {"token"}."""
    subscriber = Subscriber.find_by_token(_text(_read_body(request).get("token")))
    if subscriber is None:
        return JsonResponse({"status": "invalid_token"}, status=404)
    subscriber.confirm()
    # An unsubscribed address stays unsubscribed: an old link must not resubscribe anyone.
    status = "unsubscribed" if subscriber.status == Subscriber.UNSUBSCRIBED else "subscribed"
    return JsonResponse({"status": status, "email": subscriber.email})


@csrf_exempt  # Mail clients POST here without a CSRF token (RFC 8058 one-click).
@require_http_methods(["GET", "POST"])
def unsubscribe(request):
    """
    POST /api/v2/newsletter/unsubscribe/?token=... unsubscribes. The token may also be in
    the body. GET never unsubscribes (mail scanners open links): it redirects to the
    frontend page that asks for a click.
    """
    if request.method == "GET":
        query = urlencode({"token": request.GET["token"]}) if "token" in request.GET else ""
        response = HttpResponse(status=302)
        response["Location"] = "/newsletter/unsubscribe/" + (f"?{query}" if query else "")
        return response

    data = _read_body(request)
    token = _text(request.GET.get("token")) or _text(data.get("token"))
    subscriber = Subscriber.find_by_token(token)
    if subscriber is not None:
        subscriber.unsubscribe()
    status = "unsubscribed" if subscriber else "invalid_token"

    # JSON from the frontend, and the one-click POST from mail clients, get JSON back.
    one_click = data.get("List-Unsubscribe") == "One-Click"
    if _is_json(request) or one_click:
        body = {"status": status}
        if subscriber:
            body["email"] = subscriber.email
        return JsonResponse(body, status=200 if subscriber else 404)
    return _see_other(f"/newsletter/unsubscribe/?{urlencode({'status': status})}")
