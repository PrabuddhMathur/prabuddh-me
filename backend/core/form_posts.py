"""
Helpers shared by the public JSON endpoints that accept a form post (newsletter signup,
comments): read the body, look at the client, throttle, redirect.

The Nuxt frontend sends JSON. Plain HTML form posts also work, for visitors without
JavaScript: those get a 303 redirect to a frontend page that shows the outcome.
"""

import json

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse

MAX_EMAIL_LENGTH = 254
THROTTLE_WINDOW = 60 * 60  # seconds


def is_json(request):
    return request.content_type == "application/json"


def read_body(request):
    """The request's fields as a dict, from a JSON body or an HTML form."""
    if is_json(request):
        try:
            data = json.loads(request.body or b"{}")
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    return request.POST.dict()


def text(value):
    """The value when it is a string, else "" (JSON can send numbers, lists, null)."""
    return value if isinstance(value, str) else ""


def client_ip(request):
    # Caddy sets X-Real-IP to the visitor's address; without a proxy fall back to the socket.
    return request.headers.get("X-Real-IP") or request.META.get("REMOTE_ADDR", "")


def throttled(request, scope, limit, window=THROTTLE_WINDOW):
    """Counts this request against the client's limit for `scope`. True when over it."""
    key = f"{scope}:{client_ip(request)}"
    cache.add(key, 0, window)  # Only sets the expiry when the key is new.
    try:
        count = cache.incr(key)
    except ValueError:  # The key expired between the two calls.
        cache.set(key, 1, window)
        count = 1
    return count > limit


def see_other(url):
    """A 303 redirect, so the browser follows a POST with a GET."""
    response = HttpResponse(status=303)
    response["Location"] = url
    return response


def clean_email(value):
    """The address stripped and lower-cased, or None when it isn't a valid one."""
    email = text(value).strip().lower()
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return None
    try:
        validate_email(email)
    except ValidationError:
        return None
    return email
