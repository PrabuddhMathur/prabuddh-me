"""Newsletter subscribers, the posts emailed to them, and the queue of emails to send."""

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def make_token():
    """A random, unguessable token for the confirm and unsubscribe links."""
    return secrets.token_urlsafe(32)


class Subscriber(models.Model):
    """Someone who asked for new posts by email. Starts pending until they confirm."""

    PENDING = "pending"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    STATUS_CHOICES = [
        (PENDING, "Waiting for confirmation"),
        (SUBSCRIBED, "Subscribed"),
        (UNSUBSCRIBED, "Unsubscribed"),
    ]

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    # One token for both the confirm and the unsubscribe link. It never changes.
    token = models.CharField(max_length=64, unique=True, editable=False, default=make_token)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True, editable=False)
    confirmed_at = models.DateTimeField(null=True, blank=True, editable=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # To notice a status change however it was made (a method or the admin form).
        self._saved_status = None if self._state.adding else self.__dict__.get("status")

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.normalise(self.email)
        if self.status != self._saved_status:
            now = timezone.now()
            if self.status == self.SUBSCRIBED:
                self.confirmed_at = now
            elif self.status == self.UNSUBSCRIBED:
                self.unsubscribed_at = now
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = {
                    *kwargs["update_fields"],
                    "confirmed_at",
                    "unsubscribed_at",
                }
        super().save(*args, **kwargs)
        self._saved_status = self.status

    @staticmethod
    def normalise(email):
        return (email or "").strip().lower()

    @classmethod
    def find(cls, email):
        """The subscriber with this address (any case, any surrounding spaces), or None."""
        return cls.objects.filter(email=cls.normalise(email)).first()

    @classmethod
    def find_by_token(cls, token):
        return cls.objects.filter(token=token).first() if token else None

    def confirm(self):
        """Pending becomes subscribed. Others stay as they are: an old link mustn't resubscribe."""
        if self.status == self.PENDING:
            self.status = self.SUBSCRIBED
            self.save()

    def unsubscribe(self):
        if self.status != self.UNSUBSCRIBED:
            self.status = self.UNSUBSCRIBED
            self.save()


class Issue(models.Model):
    """One blog post emailed to the subscribers. A post has at most one."""

    post = models.OneToOneField(
        "blog.BlogPage", on_delete=models.CASCADE, related_name="newsletter_issue"
    )
    # The post title when it was queued.
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        # What the admin calls them. The "add" permission is the one that allows sending a post.
        verbose_name = "sent post"
        verbose_name_plural = "sent posts"

    def __str__(self):
        return self.subject


class Delivery(models.Model):
    """One issue going to one subscriber. The worker works through the queued ones."""

    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    STATUS_CHOICES = [
        (QUEUED, "Queued"),
        (SENDING, "Sending"),
        (SENT, "Sent"),
        (FAILED, "Failed"),
        (SKIPPED, "Skipped"),
    ]

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="deliveries")
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name="deliveries")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=QUEUED, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "deliveries"
        constraints = [
            models.UniqueConstraint(fields=["issue", "subscriber"], name="one_delivery_per_issue")
        ]

    def __str__(self):
        return f"{self.issue} to {self.subscriber}"
