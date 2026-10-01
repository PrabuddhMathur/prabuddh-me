"""The "Email subscribers" page of a blog post in the Wagtail admin."""

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from wagtail.admin import messages
from wagtail.admin.auth import permission_denied

from blog.models import BlogPage

from . import emails, sending
from .models import Delivery, Issue, Subscriber

SEND_PERMISSION = "newsletter.add_issue"
RECENT_ERRORS = 5


def post_newsletter_url(page):
    return reverse("newsletter:post", args=[page.pk])


def subscribed_count():
    return Subscriber.objects.filter(status=Subscriber.SUBSCRIBED).count()


def _send_test(request, post):
    address = request.POST.get("address", "").strip()
    try:
        validate_email(address)
    except ValidationError:
        messages.error(request, "Enter a valid email address for the test.")
        return
    try:
        emails.build_issue(post, to=[address], test=True).send()
    except Exception as exc:  # Show the mail server's complaint instead of a 500 page.
        messages.error(request, f"The test email couldn't be sent: {type(exc).__name__}: {exc}")
    else:
        messages.success(request, f"A test email was sent to {address}.")


def _queue(request, post):
    try:
        issue = sending.queue_issue(post, request.user)
    except sending.QueueError as exc:
        messages.error(request, str(exc))
        return
    total = issue.deliveries.count()
    messages.success(
        request,
        f"Queued for {total} subscriber{'s' if total != 1 else ''}. "
        "The worker sends them in the background.",
    )


def _retry(request, issue):
    count = sending.retry_failed(issue)
    messages.success(request, f"{count} failed email{'s' if count != 1 else ''} queued again.")


def post_newsletter(request, page_id):
    """Preview, test send and send for one post; after sending, the progress."""
    if not request.user.has_perm(SEND_PERMISSION):
        return permission_denied(request)
    post = get_object_or_404(BlogPage, pk=page_id)
    issue = Issue.objects.filter(post=post).first()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "test":
            _send_test(request, post)
        elif action == "send":
            _queue(request, post)
        elif action == "retry" and issue is not None:
            _retry(request, issue)
        return redirect(post_newsletter_url(post))

    context = {
        "post": post,
        "issue": issue,
        "edit_url": reverse("wagtailadmin_pages:edit", args=[post.pk]),
    }
    if issue is None:
        preview = emails.build_issue(post, to=[request.user.email or "you@example.com"])
        context.update(
            subscriber_count=subscribed_count(),
            preview_html=emails.html_of(preview),
            test_address=request.user.email,
        )
    else:
        counts = {
            row["status"]: row["n"]
            for row in issue.deliveries.values("status").annotate(n=Count("id"))
        }
        context.update(
            counts=[
                (label, counts.get(value, 0))
                for value, label in Delivery.STATUS_CHOICES
                if counts.get(value, 0) or value in (Delivery.SENT, Delivery.QUEUED)
            ],
            total=sum(counts.values()),
            failed=counts.get(Delivery.FAILED, 0),
            errors=issue.deliveries.exclude(last_error="")
            .select_related("subscriber")
            .order_by("-updated_at")[:RECENT_ERRORS],
        )
    return render(request, "newsletter/admin/post.html", context)
