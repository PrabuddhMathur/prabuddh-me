"""
Keeps the comments table tidy and what it knows about visitors short-lived. Run by the
newsletter worker about once an hour, or by hand with `manage.py comments_cleanup`.
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Comment

# Spam is deleted, and the visitor details of the other comments are cleared, this long
# after they were posted or reviewed.
KEEP_FOR = timedelta(days=30)


def purge(now=None):
    """Does the housekeeping. Returns how many comments it deleted and how many it cleared."""
    cutoff = (now or timezone.now()) - KEEP_FOR

    # Counted from when the owner marked it, so an old comment marked as spam today can
    # still be rescued for a month; spam Akismet caught, which nobody reviewed, from
    # when it was posted.
    _, deleted = (
        Comment.objects.filter(status=Comment.SPAM)
        .filter(Q(reviewed_at__lt=cutoff) | Q(reviewed_at__isnull=True, created_at__lt=cutoff))
        .delete()
    )

    # IP address, browser and referrer exist only to report to Akismet. Once the owner has
    # decided about a comment and a month has passed, they have no use.
    cleared = (
        Comment.objects.exclude(status=Comment.SPAM)
        .filter(reviewed_at__lt=cutoff)
        .filter(Q(ip_address__isnull=False) | ~Q(user_agent="") | ~Q(referrer=""))
        .update(ip_address=None, user_agent="", referrer="")
    )
    return {"spam_deleted": deleted.get(Comment._meta.label, 0), "details_cleared": cleared}
