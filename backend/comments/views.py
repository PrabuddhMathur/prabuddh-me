"""
The public comments API (see config/urls.py): list a post's comments, post one, and the
confirm and stop links of the reply-alert emails.

The Nuxt frontend sends JSON. Plain HTML form posts also work, for visitors without
JavaScript: they get a 303 redirect back to the post, where the frontend shows the outcome.
"""

import logging
import time
from datetime import UTC
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from wagtail.models import Site

from blog.models import BlogPage
from core.form_posts import clean_email, is_json, read_body, see_other, text, throttled

from . import spam
from .models import Comment, CommentSettings
from .text import EMAIL_INVALID, PARENT_UNAVAILABLE, clean_body, clean_name

logger = logging.getLogger(__name__)

# A form posted sooner than this after it was shown wasn't filled in by a person.
MIN_FORM_AGE = 3  # seconds
_signer = signing.TimestampSigner(salt="comments.form")

JSON_STATUS_CODES = {
    "pending": 200,
    "invalid": 400,
    "closed": 403,
    "not_found": 404,
    "rate_limited": 429,
}


def _now():
    return time.time()


def make_form_token(issued_at=None):
    """
    A signed time stamp that goes into the comment form. Posting it back proves that the
    form was loaded from this site, and how long ago. It never expires, so a tab left open
    overnight still works.
    """
    return _signer.sign(str(int(issued_at if issued_at is not None else _now())))


def form_token_age(token):
    """Seconds since the form token was made, or None when it isn't one of ours."""
    try:
        return _now() - int(_signer.unsign(token, max_age=None))
    except signing.BadSignature, ValueError:
        return None


def _live_post(post_id):
    """The live, public post with this id (a string or number), or None."""
    try:
        return BlogPage.objects.live().public().filter(pk=int(post_id)).first()
    except TypeError, ValueError, OverflowError:
        return None


def _comment_settings():
    site = Site.objects.filter(is_default_site=True).first()
    # Without a site there is nothing to store settings against; use the defaults.
    return CommentSettings.for_site(site) if site else CommentSettings()


def _iso(moment):
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _visible_threads(post):
    """
    (count, threads) of the post's public comments: each top-level comment with all the
    replies of its thread flattened under it, oldest first. A reply only shows when every
    comment above it does, so hiding a comment hides what was said under it.
    """
    rows = Comment.objects.filter(post=post, status=Comment.APPROVED).values(
        "id", "name", "body", "created_at", "is_author", "liked", "parent_id", "root_id"
    )
    # A parent is always older than its replies, so one pass in this order is enough.
    visible = {}
    threads = {}
    for row in rows.order_by("created_at", "id"):
        parent_id = row["parent_id"]
        if parent_id is not None and parent_id not in visible:
            continue
        visible[row["id"]] = row
        item = {
            "id": row["id"],
            "name": row["name"],
            "body": row["body"],
            "created_at": _iso(row["created_at"]),
            "is_author": row["is_author"],
            "liked": row["liked"],
        }
        if parent_id is None:
            threads[row["id"]] = {**item, "replies": []}
        else:
            parent = visible[parent_id]
            item["reply_to"] = (
                None
                if parent["id"] == row["root_id"]
                else {"id": parent["id"], "name": parent["name"]}
            )
            threads[row["root_id"]]["replies"].append(item)
    return len(visible), list(threads.values())


def _list(request):
    post = _live_post(request.GET.get("post"))
    if post is None:
        return JsonResponse({"status": "not_found"}, status=404)
    comment_settings = _comment_settings()
    enabled = comment_settings.enabled
    count, threads = _visible_threads(post) if enabled else (0, [])
    return JsonResponse(
        {
            "enabled": enabled,
            "open": enabled and post.allow_comments,
            "like_label": comment_settings.like_label,
            "akismet": spam.is_configured(),
            "count": count,
            "form_token": make_form_token(),
            "comments": threads,
        }
    )


def _truthy(value):
    return value is True or text(value).strip().lower() in {"on", "true", "1", "yes"}


def _parent_of(post, value):
    """The approved comment on this post with this id, or None."""
    try:
        return Comment.objects.filter(pk=int(value), post=post, status=Comment.APPROVED).first()
    except TypeError, ValueError, OverflowError:
        return None


def _post_comment(request):
    """
    Handles one comment and returns (status, post, errors): the status string, the post
    when it is known, and the problems with the fields (for "invalid").
    """
    if throttled(request, "comments-post", settings.COMMENTS_POST_LIMIT):
        return "rate_limited", None, {}
    data = read_body(request)

    # Bots: a filled-in honeypot, or a form that is missing its token or was posted
    # within moments of being shown. They get the same answer as everyone, and nothing is stored.
    age = form_token_age(text(data.get("form_token")))
    if text(data.get("website")).strip() or age is None or age < MIN_FORM_AGE:
        return "pending", None, {}

    post = _live_post(data.get("post"))
    if post is None:
        return "not_found", None, {}
    if not (_comment_settings().enabled and post.allow_comments):
        return "closed", post, {}

    errors = {}
    name, error = clean_name(text(data.get("name")))
    if error:
        errors["name"] = error
    email = clean_email(data.get("email"))
    if email is None:
        errors["email"] = EMAIL_INVALID
    body, error = clean_body(text(data.get("body")))
    if error:
        errors["body"] = error
    parent = None
    if data.get("parent") not in (None, ""):
        parent = _parent_of(post, data["parent"])
        if parent is None:
            errors["parent"] = PARENT_UNAVAILABLE
    if errors:
        return "invalid", post, errors

    comment = Comment(
        post=post,
        parent=parent,
        name=name,
        email=email,
        body=body,
        reply_alerts=(
            Comment.ALERTS_REQUESTED if _truthy(data.get("notify_replies")) else Comment.ALERTS_OFF
        ),
        # The visitor's address and browser are only kept to report the owner's decision
        # to Akismet, so without Akismet they aren't kept at all (see housekeeping.py).
        **(spam.request_details(request) if spam.is_configured() else {}),
    )
    verdict = spam.check(comment, request, post)
    if verdict == spam.DISCARD:  # Blatant spam: Akismet asks us not to keep even a record.
        return "pending", post, {}
    if verdict == spam.SPAM:
        comment.status = Comment.SPAM
        comment.spam_check = Comment.SPAM
    elif verdict == spam.HAM:
        comment.spam_check = Comment.HAM
    comment.save()
    return "pending", post, {}


@csrf_exempt  # Called by the public site's form; the honeypot, form token and throttle guard it.
@require_http_methods(["GET", "POST"])
def comments(request):
    """
    GET /api/v2/comments/?post=<page id> lists the post's public comments.
    POST /api/v2/comments/ adds one: post, parent (optional), name, email, body,
    notify_replies, website (the honeypot) and form_token.
    """
    if request.method == "GET":
        return _list(request)
    status, post, errors = _post_comment(request)
    if is_json(request):
        body = {"status": status}
        if errors:
            body["errors"] = errors
        return JsonResponse(body, status=JSON_STATUS_CODES[status])
    data = read_body(request)
    if post is None:  # Not looked up yet (the limit, a bot), or really not found.
        post = _live_post(data.get("post"))
    if post is None:
        return see_other("/")
    query = {"comment": status}
    # A reply that didn't go through lands on the same reply form again.
    parent = text(data.get("parent"))
    if status != "pending" and parent.isdigit():
        query["replyto"] = parent
    return see_other(f"{post.get_date_url()}?{urlencode(query)}#comment-form")


def _alerts_response(comment, status):
    post = comment.post
    return JsonResponse(
        {"status": status, "post": {"title": post.title, "url": post.get_date_url()}}
    )


@csrf_exempt
@require_POST
def alerts_confirm(request):
    """POST /api/v2/comments/alerts/confirm/ with {"token"}: turns reply alerts on."""
    token = text(read_body(request).get("token"))
    comment = Comment.objects.select_related("post").filter(token=token).first() if token else None
    if comment is None:
        return JsonResponse({"status": "invalid_token"}, status=404)
    if comment.reply_alerts != Comment.ALERTS_ON:
        comment.reply_alerts = Comment.ALERTS_ON
        comment.save(update_fields=["reply_alerts"])
    return _alerts_response(comment, "on")


@csrf_exempt  # Mail clients POST here without a CSRF token (RFC 8058 one-click).
@require_http_methods(["GET", "POST"])
def alerts_stop(request):
    """
    POST /api/v2/comments/alerts/stop/?token=... turns reply alerts off. The token may also
    be in the body. GET never changes anything (mail scanners open links): it redirects to
    the frontend page that asks for a click.
    """
    if request.method == "GET":
        query = urlencode({"token": request.GET["token"]}) if "token" in request.GET else ""
        response = HttpResponse(status=302)
        response["Location"] = "/comments/alerts/stop/" + (f"?{query}" if query else "")
        return response

    data = read_body(request)
    token = text(request.GET.get("token")) or text(data.get("token"))
    comment = Comment.objects.select_related("post").filter(token=token).first() if token else None
    if comment is not None and comment.reply_alerts != Comment.ALERTS_OFF:
        comment.reply_alerts = Comment.ALERTS_OFF
        comment.save(update_fields=["reply_alerts"])
    status = "off" if comment else "invalid_token"

    # JSON from the frontend, and the one-click POST from mail clients, get JSON back.
    one_click = data.get("List-Unsubscribe") == "One-Click"
    if is_json(request) or one_click:
        if comment is None:
            return JsonResponse({"status": status}, status=404)
        return _alerts_response(comment, status)
    return see_other(f"/comments/alerts/stop/?{urlencode({'status': status})}")
