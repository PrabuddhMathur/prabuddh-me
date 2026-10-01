"""
The sending queue. Queueing a post creates one Delivery per active subscriber; the
newsletter_worker command then calls send_due() over and over to send them: slowly,
with retries, and without ever sending the same email twice.
"""

import logging
import time
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.mail import get_connection
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import emails
from .models import Delivery, Issue, Subscriber

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
# The first retry waits this long; each further one waits twice as long as the one before.
RETRY_BASE_DELAY = timedelta(minutes=5)
# A delivery stuck in "sending" this long means the worker died mid-send.
STALE_SENDING_AFTER = timedelta(minutes=15)
# This many failures in a row means the mail server, not the recipients, is the problem.
STOP_AFTER_CONSECUTIVE_FAILURES = 3
# How long the whole queue pauses after that.
PAUSE_AFTER_STOP = timedelta(minutes=5)


class QueueError(Exception):
    """The post can't be queued; the message is meant to be shown to the editor."""


def queue_issue(post, user):
    """Creates the Issue for a post and a queued Delivery for every active subscriber."""
    if not post.live:
        raise QueueError("Publish the post first.")
    try:
        with transaction.atomic():
            if Issue.objects.filter(post=post).exists():
                raise QueueError("This post has already been emailed.")
            issue = Issue.objects.create(
                post=post, subject=post.title, created_by=user if user.pk else None
            )
            Delivery.objects.bulk_create(
                Delivery(issue=issue, subscriber=subscriber)
                for subscriber in Subscriber.objects.filter(status=Subscriber.SUBSCRIBED)
            )
    except IntegrityError:  # Two editors clicking at once: the database allows one issue per post.
        raise QueueError("This post has already been emailed.") from None
    return issue


def retry_failed(issue):
    """Puts the failed deliveries of an issue back in the queue. Returns how many."""
    return issue.deliveries.filter(status=Delivery.FAILED).update(
        status=Delivery.QUEUED,
        attempts=0,
        next_attempt_at=timezone.now(),
        updated_at=timezone.now(),
    )


def _skip_reason(delivery):
    if delivery.subscriber.status != Subscriber.SUBSCRIBED:
        return "The subscriber is no longer subscribed."
    if not delivery.issue.post.live:
        return "The post is no longer live."
    return ""


def _close_quietly(connection):
    try:
        connection.close()
    except Exception:  # Closing a broken connection can fail as well; it is dropped either way.
        pass


def _record_failure(delivery, exc):
    delivery.attempts += 1
    delivery.last_error = f"{type(exc).__name__}: {exc}"[:500]
    if delivery.attempts >= MAX_ATTEMPTS:
        delivery.status = Delivery.FAILED
    else:
        delivery.status = Delivery.QUEUED
        delivery.next_attempt_at = timezone.now() + RETRY_BASE_DELAY * 2 ** (delivery.attempts - 1)
    delivery.save(
        update_fields=["attempts", "last_error", "status", "next_attempt_at", "updated_at"]
    )


@dataclass
class BatchResult:
    """What one batch did: emails sent, attempts that failed, rows skipped."""

    sent: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def handled(self):
        return self.sent + self.failed + self.skipped


def send_due(batch_size=50):
    """Sends up to batch_size queued emails that are due. Returns how many were sent."""
    return send_batch(batch_size).sent


def send_batch(batch_size=50):
    """Like send_due, but says what else happened. The worker uses this."""
    result = BatchResult()
    now = timezone.now()
    # A crashed worker leaves rows in "sending"; put them back.
    Delivery.objects.filter(
        status=Delivery.SENDING, updated_at__lt=now - STALE_SENDING_AFTER
    ).update(status=Delivery.QUEUED, updated_at=now)

    due = list(
        Delivery.objects.filter(status=Delivery.QUEUED, next_attempt_at__lte=now)
        .select_related("issue__post", "subscriber")
        .order_by("id")[:batch_size]
    )
    if not due:
        return result

    failures_in_a_row = 0
    connection = get_connection()  # One connection for the whole batch.
    try:
        for delivery in due:
            # Claim it first, so a second worker (or an overlapping run) skips it.
            claimed = Delivery.objects.filter(pk=delivery.pk, status=Delivery.QUEUED).update(
                status=Delivery.SENDING, updated_at=timezone.now()
            )
            if not claimed:
                continue

            if reason := _skip_reason(delivery):
                delivery.status = Delivery.SKIPPED
                delivery.last_error = reason
                delivery.save(update_fields=["status", "last_error", "updated_at"])
                result.skipped += 1
                continue

            try:
                # Opened here rather than by send(), which would connect and log in again for
                # every email. Does nothing while the connection is open.
                connection.open()
                message = emails.build_issue(
                    delivery.issue.post, delivery.subscriber, connection=connection
                )
                message.send()
            except Exception as exc:
                # The error may have broken the connection; the next email opens a new one.
                _close_quietly(connection)
                logger.warning("Newsletter email to delivery %s failed: %s", delivery.pk, exc)
                _record_failure(delivery, exc)
                result.failed += 1
                failures_in_a_row += 1
                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILURES:
                    # Don't burn everyone's attempts on a broken connection or a used-up quota:
                    # leave the rest queued, and pause the whole queue for a while.
                    logger.error(
                        "Stopping the batch after %s failures in a row.", failures_in_a_row
                    )
                    Delivery.objects.filter(
                        status=Delivery.QUEUED, next_attempt_at__lte=timezone.now()
                    ).update(next_attempt_at=timezone.now() + PAUSE_AFTER_STOP)
                    break
            else:
                failures_in_a_row = 0
                delivery.status = Delivery.SENT
                delivery.sent_at = timezone.now()
                delivery.last_error = ""
                delivery.save(update_fields=["status", "sent_at", "last_error", "updated_at"])
                result.sent += 1

            time.sleep(settings.NEWSLETTER_SEND_DELAY)
    finally:
        _close_quietly(connection)
    return result
