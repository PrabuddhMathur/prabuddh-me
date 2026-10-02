"""Reader comments on blog posts, and the settings that switch them on and off."""

import secrets

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from core.emails import frontend_url


def make_token():
    """A random, unguessable token for a comment's reply-alert confirm and stop links."""
    return secrets.token_urlsafe(32)


class Comment(models.Model):
    """
    A comment on a post, or a reply to another comment. Everyone's starts out pending;
    only approved comments are public. The owner moderates in the Wagtail admin.
    """

    PENDING = "pending"
    APPROVED = "approved"
    SPAM = "spam"
    STATUS_CHOICES = [
        (PENDING, "Waiting for review"),
        (APPROVED, "Approved"),
        (SPAM, "Spam"),
    ]

    # What Akismet said when the comment was posted.
    UNCHECKED = "unchecked"
    HAM = "ham"
    SPAM_CHECK_CHOICES = [
        (UNCHECKED, "Not checked"),
        (HAM, "Not spam"),
        (SPAM, "Spam"),
    ]

    # Whether the commenter gets an email when someone replies. They ask for it with a
    # checkbox ("requested"); it only starts ("on") after they click the link in the
    # email sent when the comment goes live.
    ALERTS_OFF = "off"
    ALERTS_REQUESTED = "requested"
    ALERTS_ON = "on"
    ALERTS_CHOICES = [
        (ALERTS_OFF, "Off"),
        (ALERTS_REQUESTED, "Asked for, not confirmed"),
        (ALERTS_ON, "On"),
    ]

    post = models.ForeignKey("blog.BlogPage", on_delete=models.CASCADE, related_name="comments")
    # The comment this one answers. Replies are shown flat under the top-level comment
    # of their thread (the root), with "Replying to ..." when they answer another reply.
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    # None for a top-level comment. Kept in step with the parent by save().
    root = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="thread_replies",
        editable=False,
    )

    name = models.CharField(max_length=80)
    # Never shown. Blank only for the owner's own replies when their account has no email.
    email = models.EmailField(max_length=254, blank=True)
    body = models.TextField(help_text="Plain text.")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    spam_check = models.CharField(
        "Akismet verdict", max_length=10, choices=SPAM_CHECK_CHOICES, default=UNCHECKED
    )
    is_author = models.BooleanField(
        "Written by the author", default=False, help_text="Written by you from the admin."
    )
    liked = models.BooleanField(
        default=False, help_text="Your heart: shown as a badge next to the comment."
    )
    reply_alerts = models.CharField(max_length=10, choices=ALERTS_CHOICES, default=ALERTS_OFF)
    # For the reply-alert confirm and stop links. It never changes.
    token = models.CharField(max_length=64, unique=True, editable=False, default=make_token)

    # Kept only so spam and not-spam reports can go to Akismet; housekeeping clears them.
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    referrer = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # When the owner approved it or marked it as spam.
    reviewed_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["post", "status"])]

    def __str__(self):
        return f"{self.name} on {self.post.title}"

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        update_fields = kwargs.get("update_fields")
        if update_fields is None or "parent" in update_fields:
            parent = self.parent if self.parent_id else None
            self.root_id = (parent.root_id or parent.pk) if parent else None
            if update_fields is not None:
                kwargs["update_fields"] = {*update_fields, "root"}
        super().save(*args, **kwargs)

    def excerpt(self, length=80):
        """The start of the text on one line, for lists and emails."""
        text = " ".join(self.body.split())
        return text if len(text) <= length else text[: length - 1].rstrip() + "…"

    excerpt.short_description = "Comment"
    excerpt.admin_order_field = "body"

    def public_url(self):
        """The comment on the public site: the post's page, scrolled to the comment."""
        return frontend_url(f"{self.post.get_date_url()}#comment-{self.pk}")


@register_setting(icon="comment")
class CommentSettings(BaseSiteSetting):
    enabled = models.BooleanField(
        default=True,
        help_text=(
            "Show comments and the comment form on posts. Turning this off hides them "
            "everywhere; nothing is deleted."
        ),
    )
    like_label = models.CharField(
        max_length=100,
        default="Liked by Prabuddh",
        help_text="Shown on comments you've liked.",
    )

    panels = [FieldPanel("enabled"), FieldPanel("like_label")]

    class Meta:
        verbose_name = "Comments"

    def __str__(self):
        return "Comment settings"
