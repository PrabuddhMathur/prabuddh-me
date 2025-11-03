"""
Management command to recalculate reading times for all blog posts.
Usage: python manage.py recalculate_reading_times
"""
from django.core.management.base import BaseCommand
from blog.models import BlogPage


class Command(BaseCommand):
    help = 'Recalculates estimated reading times for all blog posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all blog posts
        blog_posts = BlogPage.objects.all()
        total_posts = blog_posts.count()
        
        if total_posts == 0:
            self.stdout.write(self.style.WARNING('No blog posts found.'))
            return
        
        self.stdout.write(f'Found {total_posts} blog post(s) to process...\n')
        
        updated_count = 0
        
        for post in blog_posts:
            old_time = post.estimated_reading_time
            
            # Calculate word count from intro and body
            word_count = len(post.intro.split())
            
            # Count words in StreamField blocks
            for block in post.body:
                if hasattr(block.value, 'source'):  # RichTextBlock
                    word_count += len(block.value.source.split())
                elif hasattr(block.value, 'get'):
                    # StructBlock - check for text fields
                    for key, value in block.value.items():
                        if isinstance(value, str):
                            word_count += len(value.split())
            
            # Calculate reading time (200 words per minute, minimum 1 minute)
            new_time = max(1, round(word_count / 200))
            
            if old_time != new_time:
                self.stdout.write(
                    f'  "{post.title}": {word_count} words → '
                    f'{old_time} min → {new_time} min'
                )
                
                if not dry_run:
                    post.estimated_reading_time = new_time
                    # Use update_fields to avoid triggering the full save() logic
                    post.save(update_fields=['estimated_reading_time'])
                
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ "{post.title}": {new_time} min (no change needed)'
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would update {updated_count} of {total_posts} post(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully updated {updated_count} of {total_posts} post(s)'
                )
            )
