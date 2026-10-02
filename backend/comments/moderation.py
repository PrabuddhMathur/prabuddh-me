"""
What the owner can do to a comment. Every admin action (a row's buttons, the bulk actions,
the reply page) goes through these functions, so the side effects, which are telling
Akismet and sending the reply-alert emails, live in one place.

Emails that can't be sent never undo the action: each failure is logged and returned as
a warning for the admin to show.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field

from django.core.mail import get_connection
from django.utils import timezone
from wagtail.models import Site

from core.models import AuthorSettings

from . import emails, spam
from .models import Comment

logger = logging.getLogger(__name__)


class Effects:
    """
    What one admin action does outside the database: the emails, over one mail connection
    that is opened for the first email only (most actions send none), and the reports to
    Akismet, with the warnings for the owner.

    Once the mail server can't be reached, or Akismet fails, the rest of the action leaves
    it alone: every try could wait for the whole timeout, and a bulk action would run past
    the server's time limit for a request.
    """

    def __init__(self):
        self.warnings = []
        self.connection = get_connection()
        self.mail_error = None
        self.akismet_failed = False

    def send(self, build, *args):
        """Sends the email build(*args, connection) makes."""
        message = build(*args, self.connection)
        to = ", ".join(message.to)
        if self.mail_error is None:
            try:
                self.connection.open()  # Connects for the first email; does nothing after.
            except Exception as exc:
                logger.exception("Couldn't connect to the mail server")
                self.mail_error = f"{type(exc).__name__}: {exc}"
        if self.mail_error is not None:
            self.warnings.append(
                f"The email to {to} couldn't be sent: the mail server couldn't be reached "
                f"({self.mail_error})."
            )
            return
        try:
            message.send()
        except Exception as exc:
            logger.exception("Couldn't send a comment email to %s", to)
            self.warnings.append(
                f"The email to {to} couldn't be sent ({type(exc).__name__}: {exc})."
            )
            # The error may have broken the connection; the next email opens a new one.
            self.close()

    def report(self, report, comment):
        """Tells Akismet about one of the owner's decisions (report_spam or report_ham)."""
        if not self.akismet_failed and report(comment) is False:
            self.akismet_failed = True

    def close(self):
        try:
            self.connection.close()
        except Exception:  # Closing a broken connection can fail as well; it is dropped either way.
            pass


@contextmanager
def _effects(given):
    """The caller's Effects, or one for this call alone, closed at the end."""
    if given is not None:
        yield given
        return
    effects = Effects()
    try:
        yield effects
    finally:
        effects.close()


def _send_emails(comment, effects):
    """
    The emails a comment going live causes.

    - Its author asked for reply alerts (and isn't the site's owner): one email asking them
      to confirm. The alerts only start once they click the link in it.
    - It answers a comment whose author turned reply alerts on: a reply alert to them,
      unless they are replying to themselves.
    """
    if comment.reply_alerts == Comment.ALERTS_REQUESTED and not comment.is_author:
        if comment.email:
            effects.send(emails.build_alerts_confirmation, comment)
    parent = comment.parent
    if (
        parent is not None
        and parent.reply_alerts == Comment.ALERTS_ON
        and parent.status == Comment.APPROVED
        and not parent.is_author
        and parent.email
        and parent.email != comment.email
    ):
        effects.send(emails.build_reply_alert, comment)


def approve(comment, effects=None):
    """
    Makes a comment public. Does nothing to a comment that already is. Tells Akismet when it
    called the comment spam, and sends the emails that going live causes. Returns the warnings.
    """
    with _effects(effects) as effects:
        if comment.status != Comment.APPROVED:
            was_spam = comment.status == Comment.SPAM or comment.spam_check == Comment.SPAM
            comment.status = Comment.APPROVED
            comment.reviewed_at = timezone.now()
            comment.save(update_fields=["status", "reviewed_at"])
            if was_spam:
                effects.report(spam.report_ham, comment)
            _send_emails(comment, effects)
    return effects.warnings


def mark_spam(comment, effects=None):
    """Hides a comment as spam, and tells Akismet unless it already called it spam."""
    if comment.status == Comment.SPAM:
        return
    comment.status = Comment.SPAM
    comment.reviewed_at = timezone.now()
    comment.save(update_fields=["status", "reviewed_at"])
    if comment.spam_check != Comment.SPAM:
        with _effects(effects) as effects:
            effects.report(spam.report_spam, comment)


def set_liked(comment, liked):
    """The owner's heart. Only approved comments can have one. True when something changed."""
    if comment.status != Comment.APPROVED or comment.liked == liked:
        return False
    comment.liked = liked
    comment.save(update_fields=["liked"])
    return True


def author_name():
    """The owner's name as the site shows it (Settings > Author Settings)."""
    site = Site.objects.filter(is_default_site=True).first()
    return (AuthorSettings.for_site(site) if site else AuthorSettings()).author_name


def author_reply(parent, body, user, effects=None):
    """
    The owner answers a comment, which approves it first when it is still waiting. Returns
    (the new comment, the warnings). `body` is already cleaned.
    """
    if parent.status == Comment.SPAM:
        raise ValueError("A comment marked as spam can't be replied to.")
    with _effects(effects) as effects:
        approve(parent, effects)
        reply = Comment.objects.create(
            post=parent.post,
            parent=parent,
            name=author_name(),
            email=user.email or "",
            body=body,
            status=Comment.APPROVED,
            is_author=True,
            reviewed_at=timezone.now(),
        )
        _send_emails(reply, effects)
    return reply, effects.warnings


@dataclass
class Outcome:
    """What an action did to a batch of comments."""

    changed: int = 0
    warnings: list = field(default_factory=list)


def run(action, comments):
    """
    Applies "approve", "spam", "like" or "unlike" to each of the comments, skipping the
    ones it doesn't apply to. Returns an Outcome.
    """
    outcome = Outcome()
    with _effects(None) as effects:
        for comment in comments:
            before = (comment.status, comment.liked)
            if action == "approve":
                approve(comment, effects)
            elif action == "spam":
                mark_spam(comment, effects)
            elif action in ("like", "unlike"):
                set_liked(comment, action == "like")
            else:
                raise ValueError(f"Unknown action {action!r}")
            outcome.changed += (comment.status, comment.liked) != before
    outcome.warnings = effects.warnings
    return outcome
