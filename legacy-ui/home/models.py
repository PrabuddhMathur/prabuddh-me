from django.db import models
from django.core.exceptions import ValidationError
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
import logging

# Import base blocks and models from core
from core.models import (
    BasePage,
    BaseRichTextBlock,
    BaseImageBlock,
    BaseHeroBlock,
    BaseCallToActionBlock,
    BaseAuthorBioBlock,
    BaseRecentPostsBlock,
    BaseQuoteBlock,
    BaseSpacerBlock,
)

# Configure logger
logger = logging.getLogger(__name__)


# =====================================================
# HomePage Model
# =====================================================

class HomePage(BasePage):
    """
    Production-grade Wagtail homepage with extensive StreamField usage.
    Designed for a personal blog with flexible content blocks.
    Extends BasePage to inherit SEO fields.
    
    This page can only be created once under the site root.
    """
    
    # Wagtail page configuration - singleton homepage
    max_count = 1  # Only one instance can be created
    parent_page_types = ['wagtailcore.Page']  # Can only exist under root
    
    # Hero Section Fields
    hero_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Main hero title (optional, can also use StreamField hero)",
        db_index=True,
    )
    hero_subtitle = models.CharField(
        max_length=300,
        blank=True,
        help_text="Hero subtitle or tagline"
    )
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Hero background image"
    )
    hero_cta_text = models.CharField(
        max_length=50,
        blank=True,
        help_text="Call-to-action button text"
    )
    hero_cta_link = models.URLField(
        blank=True,
        help_text="Call-to-action button link"
    )
    
    # Hero text positioning
    hero_text_horizontal = models.CharField(
        max_length=20,
        choices=[
            ('left', 'Left'),
            ('center', 'Center'),
            ('right', 'Right'),
        ],
        default='left',
        help_text="Horizontal position of hero text"
    )
    hero_text_vertical = models.CharField(
        max_length=20,
        choices=[
            ('top', 'Top'),
            ('center', 'Center'),
            ('bottom', 'Bottom'),
        ],
        default='center',
        help_text="Vertical position of hero text"
    )
    
    # Main Content StreamField - Uses blocks from core
    body = StreamField(
        [
            ('text', BaseRichTextBlock()),
            ('image', BaseImageBlock()),
            ('hero', BaseHeroBlock()),
            ('cta', BaseCallToActionBlock()),
            ('author_bio', BaseAuthorBioBlock()),
            ('recent_posts', BaseRecentPostsBlock()),
            ('quote', BaseQuoteBlock()),
            ('spacer', BaseSpacerBlock()),
        ],
        blank=True,
        use_json_field=True,
        help_text="Main page content using flexible blocks"
    )
    
    # Featured Posts Configuration
    featured_posts_title = models.CharField(
        max_length=100,
        default="Featured Posts",
        help_text="Title for the featured posts section"
    )
    number_of_featured_posts = models.IntegerField(
        default=3,
        help_text="Number of featured posts to display",
        db_index=True,
    )
    show_featured_posts = models.BooleanField(
        default=True,
        help_text="Display featured posts section",
        db_index=True,
    )
    
    # Recent Posts Configuration  
    recent_posts_title = models.CharField(
        max_length=100,
        default="Recent Posts",
        help_text="Title for the recent posts section"
    )
    number_of_recent_posts = models.IntegerField(
        default=5,
        help_text="Number of recent posts to display",
        db_index=True,
    )
    show_recent_posts = models.BooleanField(
        default=True,
        help_text="Display recent posts section",
        db_index=True,
    )
    
    # SEO and Social Sharing (inherited from BasePage)
    # meta_description, meta_keywords, og_title, og_description, og_image
    
    # Additional Settings
    show_author_sidebar = models.BooleanField(
        default=True,
        help_text="Display author information in sidebar"
    )
    enable_comments = models.BooleanField(
        default=False,
        help_text="Enable comments section"
    )
    custom_css_class = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom CSS class for styling"
    )
    
    # Wagtail Admin Configuration
    content_panels = BasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_image'),
            FieldPanel('hero_cta_text'),
            FieldPanel('hero_cta_link'),
            FieldPanel('hero_text_horizontal'),
            FieldPanel('hero_text_vertical'),
        ], heading="Hero Section"),
        
        FieldPanel('body'),
    ]
    
    # Inherit SEO panels from BasePage
    promote_panels = BasePage.promote_panels + BasePage.seo_panels
    
    settings_panels = BasePage.settings_panels + [
        MultiFieldPanel([
            FieldPanel('featured_posts_title'),
            FieldPanel('number_of_featured_posts'),
            FieldPanel('show_featured_posts'),
        ], heading="Featured Posts Settings"),
        
        MultiFieldPanel([
            FieldPanel('recent_posts_title'),
            FieldPanel('number_of_recent_posts'),
            FieldPanel('show_recent_posts'),
        ], heading="Recent Posts Settings"),
        
        MultiFieldPanel([
            FieldPanel('show_author_sidebar'),
            FieldPanel('enable_comments'),
            FieldPanel('custom_css_class'),
        ], heading="Display Settings"),
    ]
    
    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(promote_panels, heading='SEO'),
        ObjectList(settings_panels, heading='Settings'),
    ])
    
    # Template Context
    def get_context(self, request):
        """
        Add extra context for template rendering.
        Includes blog posts if available, with graceful degradation.
        """
        context = super().get_context(request)
        
        # Try to import and get blog posts (graceful fallback if blog app doesn't exist)
        try:
            from blog.models import BlogPage
            
            # Get recent posts
            if self.show_recent_posts:
                try:
                    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
                    recent_posts = (
                        BlogPage.objects
                        .live()
                        .public()
                        .select_related('owner')
                        .order_by('-first_published_at')[:self.number_of_recent_posts]
                    )
                    context['recent_posts'] = recent_posts
                    logger.debug(f"Loaded {recent_posts.count()} recent posts for homepage")
                except Exception as e:
                    logger.warning(f"Error fetching recent posts: {e}")
                    context['recent_posts'] = []
            
            # Get featured posts (assuming there's a featured field on BlogPage)
            if self.show_featured_posts:
                try:
                    # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
                    featured_posts = (
                        BlogPage.objects
                        .live()
                        .public()
                        .filter(featured=True)
                        .select_related('owner')[:self.number_of_featured_posts]
                    )
                    context['featured_posts'] = featured_posts
                    logger.debug(f"Loaded {featured_posts.count()} featured posts for homepage")
                except Exception as e:
                    # Fallback to recent posts if no featured field exists
                    logger.info(f"Featured field not available, using recent posts: {e}")
                    try:
                        # Performance: Use select_related('owner') to avoid N+1 queries when accessing post authors
                        featured_posts = (
                            BlogPage.objects
                            .live()
                            .public()
                            .select_related('owner')
                            .order_by('-first_published_at')[:self.number_of_featured_posts]
                        )
                        context['featured_posts'] = featured_posts
                    except Exception as fallback_error:
                        logger.warning(f"Error in fallback featured posts query: {fallback_error}")
                        context['featured_posts'] = []
                    
        except ImportError:
            # Blog app doesn't exist yet, set empty querysets
            logger.info("Blog app not found, setting empty post lists")
            context['recent_posts'] = []
            context['featured_posts'] = []
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error in get_context: {e}", exc_info=True)
            context['recent_posts'] = []
            context['featured_posts'] = []
        
        return context
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Homepage"
        verbose_name_plural = "Homepages"
        ordering = ['-first_published_at']
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Validate featured posts count
        if self.number_of_featured_posts < 0:
            raise ValidationError({
                'number_of_featured_posts': 'Number of featured posts cannot be negative.'
            })
        
        if self.number_of_featured_posts > 20:
            raise ValidationError({
                'number_of_featured_posts': 'Number of featured posts cannot exceed 20.'
            })
        
        # Validate recent posts count
        if self.number_of_recent_posts < 0:
            raise ValidationError({
                'number_of_recent_posts': 'Number of recent posts cannot be negative.'
            })
        
        if self.number_of_recent_posts > 50:
            raise ValidationError({
                'number_of_recent_posts': 'Number of recent posts cannot exceed 50.'
            })
        
        # Validate CTA button - both text and link must be provided together
        if self.hero_cta_text and not self.hero_cta_link:
            raise ValidationError({
                'hero_cta_link': 'CTA link is required when CTA text is provided.'
            })
        
        if self.hero_cta_link and not self.hero_cta_text:
            raise ValidationError({
                'hero_cta_text': 'CTA button text is required when CTA link is provided. Use meaningful text for screen reader users.'
            })
        
        # Validate CTA text is meaningful (not just whitespace)
        if self.hero_cta_text and not self.hero_cta_text.strip():
            raise ValidationError({
                'hero_cta_text': 'CTA button text cannot be empty or only whitespace. Use meaningful text for screen reader users.'
            })
