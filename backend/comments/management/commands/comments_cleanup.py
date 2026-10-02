"""
Deletes old spam comments and clears the visitor details of reviewed ones. The newsletter
worker does this by itself about once an hour; this is for running it by hand:

    uv run manage.py comments_cleanup
"""

from django.core.management.base import BaseCommand

from comments.housekeeping import purge


class Command(BaseCommand):
    help = "Deletes spam comments older than 30 days and clears old visitor details"

    def handle(self, *args, **options):
        counts = purge()
        self.stdout.write(
            f"Deleted {counts['spam_deleted']} spam comment(s), "
            f"cleared the visitor details of {counts['details_cleared']} comment(s)."
        )
