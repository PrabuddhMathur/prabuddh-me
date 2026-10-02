"""
Sends the queued newsletter emails. Run it next to the web server:

    uv run manage.py newsletter_worker             # forever, in production
    uv run manage.py newsletter_worker --once      # send what is due now, then exit
    uv run manage.py newsletter_worker --reload    # restart on code changes (development)

It is also the one background process the site has, so it does the comments'
housekeeping (comments.housekeeping) about once an hour.
"""

import logging
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import autoreload

from comments.housekeeping import purge
from newsletter.sending import send_batch

logger = logging.getLogger("newsletter.worker")

HOUSEKEEPING_INTERVAL = 60 * 60  # seconds


class Command(BaseCommand):
    help = "Sends the queued newsletter emails, slowly and with retries"

    # When the comment housekeeping last ran in this process (time.monotonic()).
    housekeeping_at = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--sleep",
            type=float,
            default=10,
            help="Seconds to wait when nothing is due (default 10)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Send everything that is due now, then exit",
        )
        parser.add_argument(
            "--reload",
            action="store_true",
            help="Restart when the code changes (for development)",
        )

    def handle(self, *args, **options):
        # The worker reports through logging. The production settings print every logger;
        # the development ones print none, so give the newsletter loggers a handler then
        # (only them: Django prints its own messages, such as the reloader's, already).
        newsletter_logger = logging.getLogger("newsletter")
        if not logging.getLogger().handlers and not newsletter_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
            newsletter_logger.addHandler(handler)
            newsletter_logger.setLevel(logging.INFO)
        if options["reload"] and not options["once"]:
            autoreload.run_with_reloader(self.run, **options)
        else:
            self.run(**options)

    def run(self, *, sleep, once, **options):
        logger.info("Newsletter worker started.")
        try:
            while True:
                handled = self.run_batch()
                self.run_housekeeping()
                if once and not handled:
                    return
                if not handled and not once:
                    time.sleep(sleep)
        except KeyboardInterrupt:
            logger.info("Newsletter worker stopped.")

    def run_batch(self):
        """One batch. Returns how many emails it handled; any error is logged, not raised."""
        try:
            close_old_connections()
            result = send_batch()
        except Exception:
            # Not migrated yet, database locked, ...: wait and try again, don't die.
            logger.exception("Newsletter worker batch failed")
            return 0
        if result.handled:
            logger.info(
                # Failed attempts are retried later, up to 5 per email (see sending.py).
                "Batch done: %s sent, %s failed attempts, %s skipped.",
                result.sent,
                result.failed,
                result.skipped,
            )
        return result.handled

    def run_housekeeping(self):
        """Comment housekeeping, at most once an hour. Any error is logged, not raised."""
        now = time.monotonic()
        if self.housekeeping_at is not None and now - self.housekeeping_at < HOUSEKEEPING_INTERVAL:
            return
        self.housekeeping_at = now
        try:
            counts = purge()
        except Exception:
            logger.exception("Comment housekeeping failed")
            return
        if any(counts.values()):
            logger.info(
                "Comment housekeeping: %s spam deleted, visitor details cleared on %s.",
                counts["spam_deleted"],
                counts["details_cleared"],
            )
