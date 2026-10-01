"""
Recalculates every blog post's estimated reading time, e.g. after changing how words
are counted. Usage: uv run manage.py recalculate_reading_times [--dry-run]
"""

from django.core.management.base import BaseCommand

from blog.models import BlogPage


class Command(BaseCommand):
    help = "Recalculates estimated reading times for all blog posts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        posts = BlogPage.objects.all()
        if not posts:
            self.stdout.write(self.style.WARNING("No blog posts found."))
            return

        updated = 0
        for post in posts:
            new_time = post.get_reading_time()
            if new_time == post.estimated_reading_time:
                self.stdout.write(f'  "{post.title}": {new_time} min (no change needed)')
                continue
            self.stdout.write(
                f'  "{post.title}": {post.estimated_reading_time} min → {new_time} min'
            )
            if not dry_run:
                # A plain UPDATE: no new revision, no validation, no change to the live version.
                BlogPage.objects.filter(pk=post.pk).update(estimated_reading_time=new_time)
            updated += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[DRY RUN] Would update {updated} of {len(posts)} post(s)")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} of {len(posts)} post(s)"))
