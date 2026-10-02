"""
Comment pages and actions in the Wagtail admin: the one-click actions of a row, the reply
page, and what they tell the owner afterwards. The real work is in moderation.py.
"""

from urllib.parse import urlencode

from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from wagtail.admin import messages
from wagtail.admin.auth import permission_denied
from wagtail.admin.utils import get_valid_next_url_from_request

from . import moderation
from .models import Comment
from .text import clean_body

CHANGE_PERMISSION = "comments.change_comment"
DELETE_PERMISSION = "comments.delete_comment"

# URL namespace of the viewset, see wagtail_hooks.py.
NAMESPACE = "comments"

# What to tell the owner after an action. {n} is "3 comments" (or "1 comment").
DONE_MESSAGES = {
    "approve": "Approved {n}.",
    "spam": "Marked {n} as spam.",
    "like": "Liked {n}.",
    "unlike": "Removed your like from {n}.",
}
NOTHING_TO_DO = {
    "approve": "Nothing to approve: the comment is already approved.",
    "spam": "Nothing to do: the comment is already marked as spam.",
    "like": "Only approved comments can be liked.",
    "unlike": "Nothing to do: the comment is not liked.",
}


def index_url(**query):
    """The listing, optionally filtered: index_url(status="pending")."""
    url = reverse(f"{NAMESPACE}:list")
    return f"{url}?{urlencode(query)}" if query else url


def action_url(comment, action):
    return reverse(f"{NAMESPACE}:{action}", args=[comment.pk])


def reply_url(comment):
    return reverse(f"{NAMESPACE}:reply", args=[comment.pk])


def count_phrase(count):
    return f"{count} comment{'s' if count != 1 else ''}"


def done_message(action, count):
    return DONE_MESSAGES[action].format(n=count_phrase(count))


def pending_count():
    return Comment.objects.filter(status=Comment.PENDING).count()


def show_warnings(request, warnings):
    for warning in warnings:
        messages.warning(request, warning)


@require_POST
def act(request, pk, action):
    """Approve, mark as spam, like or unlike one comment (a button in the listing)."""
    if not request.user.has_perm(CHANGE_PERMISSION):
        return permission_denied(request)
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=pk)
    outcome = moderation.run(action, [comment])
    if outcome.changed:
        messages.success(request, done_message(action, outcome.changed))
    else:
        messages.warning(request, NOTHING_TO_DO[action])
    show_warnings(request, outcome.warnings)
    return redirect(get_valid_next_url_from_request(request) or index_url())


class ReplyForm(forms.Form):
    body = forms.CharField(
        label="Your reply",
        widget=forms.Textarea(attrs={"rows": 6}),
        error_messages={"required": "Please write a reply."},
    )

    def clean_body(self):
        body, error = clean_body(self.cleaned_data["body"])
        if error:
            raise forms.ValidationError(error)
        return body


def reply(request, pk):
    """The owner answers a comment; a comment still waiting for review is approved with it."""
    if not request.user.has_perm(CHANGE_PERMISSION):
        return permission_denied(request)
    comment = get_object_or_404(Comment.objects.select_related("post", "parent"), pk=pk)
    if comment.status == Comment.SPAM:
        messages.error(request, "A comment marked as spam can't be replied to. Approve it first.")
        return redirect(index_url())

    form = ReplyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        was_pending = comment.status == Comment.PENDING
        _, warnings = moderation.author_reply(comment, form.cleaned_data["body"], request.user)
        messages.success(
            request,
            f"Your reply to {comment.name} is published"
            + (" and the comment is approved." if was_pending else "."),
        )
        show_warnings(request, warnings)
        return redirect(get_valid_next_url_from_request(request) or index_url())

    context = {
        "comment": comment,
        "form": form,
        "next": get_valid_next_url_from_request(request),
        "index_url": index_url(),
        "edit_url": reverse(f"{NAMESPACE}:edit", args=[comment.pk]),
    }
    return render(request, "comments/admin/reply.html", context)
