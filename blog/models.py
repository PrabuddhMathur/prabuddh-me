from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils.text import slugify
from django.utils import timezone
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from wagtail.search import index
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from typing import Optional, List
import logging

# Import base blocks and models from core
from core.models import (
    BasePage,
    BaseHeadingBlock,
    BaseRichTextBlock,
    BaseImageBlock,
    BaseButtonBlock,
    BaseSpacerBlock,
    BaseHeroBlock,
    BaseCallToActionBlock,
    BaseQuoteBlock,
    BaseAuthorBioBlock,
    BaseRecentPostsBlock,
)

# Configure logger
logger = logging.getLogger(__name__)


# =====================================================
# Tag Models for Blog Posts
# =====================================================

class BlogPageTag(TaggedItemBase):
    """
    Tag model for blog posts using django-taggit.
    Allows categorization and filtering of blog posts.
    """
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


# =====================================================
# Blog Page (Individual Blog Post)
# =====================================================

class BlogPage(BasePage):
    """
    Individual blog post page with rich content via StreamField.
    Extends BasePage to inherit SEO fields.
    Production-grade with validation, logging, and search indexing.
    """
    
    # Author Information
    author = models.CharField(
        max_length=100,
        default="Prabuddh Mathur",
        help_text="Post author name",
        db_index=True,
    )
    
    author_bio = RichTextField(
        blank=True,
        help_text="Author biography (optional, overrides global author bio)"
    )
    
    # Post Metadata
    date = models.DateField(
        "Post date",
        help_text="Publication date for the blog post",
        db_index=True,
    )
    
    intro = models.CharField(
        max_length=250,
        help_text="Brief introduction/excerpt (250 characters max)",
        db_index=True,
        blank=True
    )
    
    # Featured Image
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Featured image displayed in listings and at top of post"
    )
    
    featured_image_caption = models.CharField(
        max_length=250,
        blank=True,
        help_text="Optional caption for the featured image"
    )
    
    # Post Content (StreamField) - Using all core blocks
    body = StreamField([
        ('heading', BaseHeadingBlock()),
        ('text', BaseRichTextBlock()),
        ('image', BaseImageBlock()),
        ('quote', BaseQuoteBlock()),
        ('button', BaseButtonBlock()),
        ('spacer', BaseSpacerBlock()),
        ('hero', BaseHeroBlock()),
        ('cta', BaseCallToActionBlock()),
        ('author_bio', BaseAuthorBioBlock()),
        ('recent_posts', BaseRecentPostsBlock()),
    ], use_json_field=True, blank=True)
    
    # Tags
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    
    # Display Options
    featured = models.BooleanField(
        default=False,
        help_text="Mark as featured post (shown prominently on blog index)",
        db_index=True,
    )
    
    show_author_bio = models.BooleanField(
        default=True,
        help_text="Display author biography at the end of post"
    )
    
    show_related_posts = models.BooleanField(
        default=True,
        help_text="Display related posts based on tags"
    )
    
    # Reading Time (calculated field)
    estimated_reading_time = models.IntegerField(
        default=0,
        help_text="Estimated reading time in minutes (auto-calculated on save)"
    )
    
    # Search index configuration
    search_fields = BasePage.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
        index.SearchField('author'),
        index.FilterField('date'),
        index.FilterField('featured'),
    ]
    
    # Content panels
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('author'),
            FieldPanel('date'),
        ], heading="Post Metadata"),
        
        FieldPanel('intro'),
        
        MultiFieldPanel([
            FieldPanel('featured_image'),
            FieldPanel('featured_image_caption'),
        ], heading="Featured Image"),
        
        FieldPanel('body'),
        FieldPanel('tags'),
        
        MultiFieldPanel([
            FieldPanel('author_bio'),
        ], heading="Author Information"),
    ]
    
    # Settings panels
    settings_panels = Page.settings_panels + [
        MultiFieldPanel([
            FieldPanel('featured'),
            FieldPanel('show_author_bio'),
            FieldPanel('show_related_posts'),
        ], heading="Display Options"),
    ]
    
    # SEO panels from BasePage
    promote_panels = BasePage.seo_panels + Page.promote_panels
    
    # Organize into tabs
    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(promote_panels, heading='Promote'),
        ObjectList(settings_panels, heading='Settings'),
    ])
    
    # Subpage/parent page rules
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-first_published_at', '-date']
    
    def __str__(self):
        """String representation of BlogPage."""
        return self.title
    
    @classmethod
    def get_recent_posts(cls, limit: int = 5):
        """
        Get recent published blog posts.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            QuerySet of recent BlogPage objects
        """
        cache_key = f'blog_recent_posts_{limit}'
        posts = cache.get(cache_key)
        
        if posts is None:
            posts = cls.objects.live().public().order_by('-first_published_at')[:limit]
            cache.set(cache_key, posts, 900)  # Cache for 15 minutes
            logger.debug(f"Cached {limit} recent blog posts")
        
        return posts
    
    @classmethod
    def get_posts_by_tag(cls, tag_name: str, limit: Optional[int] = None):
        """
        Get blog posts by tag name.
        
        Args:
            tag_name: Tag slug or name to filter by
            limit: Optional maximum number of posts
            
        Returns:
            QuerySet of BlogPage objects with the specified tag
        """
        posts = cls.objects.live().public().filter(tags__slug=tag_name).order_by('-first_published_at')
        
        if limit:
            posts = posts[:limit]
        
        return posts
    
    @classmethod
    def get_featured_posts(cls, limit: int = 3):
        """
        Get featured blog posts.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            QuerySet of featured BlogPage objects
        """
        cache_key = f'blog_featured_posts_{limit}'
        posts = cache.get(cache_key)
        
        if posts is None:
            posts = cls.objects.live().public().filter(featured=True).order_by('-first_published_at')[:limit]
            cache.set(cache_key, posts, 900)  # Cache for 15 minutes
            logger.debug(f"Cached {limit} featured blog posts")
        
        return posts
    
    def get_author_url(self):
        """Get the URL for this post's author archive."""
        from django.utils.text import slugify
        from django.urls import reverse
        return reverse('blog_author_archive', args=[slugify(self.author)])
    
    def get_date_url(self):
        """Get the date-based URL for this post: /YYYY/MM/DD/slug/"""
        return f"/{self.date.year:04d}/{self.date.month:02d}/{self.date.day:02d}/{self.slug}/"
    
    def get_url_parts(self, request=None):
        """
        Override to generate date-based URLs: /YYYY/MM/DD/slug/
        """
        url_parts = super().get_url_parts(request)
        
        if url_parts is None:
            return None
        
        site_id, root_url, page_path = url_parts
        
        # Generate date-based path
        date_path = f"{self.date.year:04d}/{self.date.month:02d}/{self.date.day:02d}/{self.slug}/"
        
        return (site_id, root_url, date_path)
    
    def save(self, *args, **kwargs):
        """
        Override save to calculate estimated reading time.
        Assumes average reading speed of 200 words per minute.
        Also clears related caches for production-grade cache management.
        """
        try:
            # Calculate word count from intro and body
            word_count = len(self.intro.split())
            
            # Count words in StreamField blocks
            for block in self.body:
                if hasattr(block.value, 'source'):  # RichTextBlock
                    word_count += len(block.value.source.split())
                elif hasattr(block.value, 'get'):
                    # StructBlock - check for text fields
                    for key, value in block.value.items():
                        if isinstance(value, str):
                            word_count += len(value.split())
            
            # Calculate reading time (200 words per minute, minimum 1 minute)
            self.estimated_reading_time = max(1, word_count // 200)
            
            logger.info(f"Saving BlogPage: {self.title} (Reading time: {self.estimated_reading_time} min)")
            
            # Clear related caches
            cache_keys = [
                f'blog_related_posts_{self.id}',
                f'blog_posts_by_tag',
                f'blog_recent_posts',
            ]
            for key in cache_keys:
                cache.delete(key)
            
            super().save(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error saving BlogPage {self.title}: {e}", exc_info=True)
            raise
    
    def get_context(self, request, *args, **kwargs):
        """
        Add custom context to the template.
        Production-grade with error handling and caching.
        """
        context = super().get_context(request, *args, **kwargs)
        
        try:
            # Get related posts based on shared tags with caching
            if self.show_related_posts and self.tags.exists():
                cache_key = f'blog_related_posts_{self.id}'
                related_posts = cache.get(cache_key)
                
                if related_posts is None:
                    related_posts = BlogPage.objects.live().public().exclude(id=self.id)
                    # Filter by posts that share at least one tag
                    related_posts = related_posts.filter(
                        tags__in=self.tags.all()
                    ).distinct().order_by('-first_published_at')[:3]
                    
                    # Cache for 15 minutes
                    cache.set(cache_key, related_posts, 900)
                    logger.debug(f"Cached related posts for BlogPage {self.id}")
                
                context['related_posts'] = related_posts
            
            # Get previous and next posts with error handling
            all_posts = BlogPage.objects.live().public().order_by('-first_published_at')
            post_list = list(all_posts.values_list('id', flat=True))
            
            if self.id in post_list:
                current_index = post_list.index(self.id)
                
                # Previous post (older)
                if current_index < len(post_list) - 1:
                    prev_id = post_list[current_index + 1]
                    try:
                        context['prev_post'] = BlogPage.objects.get(id=prev_id)
                    except BlogPage.DoesNotExist:
                        logger.warning(f"Previous post {prev_id} not found")
                        context['prev_post'] = None
                
                # Next post (newer)
                if current_index > 0:
                    next_id = post_list[current_index - 1]
                    try:
                        context['next_post'] = BlogPage.objects.get(id=next_id)
                    except BlogPage.DoesNotExist:
                        logger.warning(f"Next post {next_id} not found")
                        context['next_post'] = None
                        
        except Exception as e:
            logger.error(f"Error in get_context for BlogPage {self.id}: {e}", exc_info=True)
            # Set defaults to prevent template errors
            context['related_posts'] = []
            context['prev_post'] = None
            context['next_post'] = None
        
        return context
    
    def clean(self):
        """
        Validate model data with comprehensive checks.
        Production-grade validation following Django best practices.
        """
        super().clean()
        
        errors = {}
        
        # Validate intro length
        if len(self.intro) > 250:
            errors['intro'] = ValidationError(
                'Introduction must be 250 characters or less.',
                code='intro_too_long'
            )
        
        # Validate reading time
        if self.estimated_reading_time < 0:
            errors['estimated_reading_time'] = ValidationError(
                'Reading time cannot be negative.',
                code='invalid_reading_time'
            )
        
        # Validate date is not in the future
        if self.date and self.date > timezone.now().date():
            errors['date'] = ValidationError(
                'Post date cannot be in the future.',
                code='future_date'
            )
        
        # Validate author name is not empty
        if not self.author or not self.author.strip():
            errors['author'] = ValidationError(
                'Author name is required.',
                code='author_required'
            )
        
        # Validate featured image has alt text if provided
        if self.featured_image and not self.featured_image_caption:
            logger.warning(f"BlogPage {self.title} has featured image but no caption (accessibility)")
        
        if errors:
            raise ValidationError(errors)
