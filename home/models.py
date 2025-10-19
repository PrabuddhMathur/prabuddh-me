from django.db import models
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList

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


# =====================================================
# HomePage Model
# =====================================================

class HomePage(BasePage):
    """
    Production-grade Wagtail homepage with extensive StreamField usage.
    Designed for a personal blog with flexible content blocks.
    Extends BasePage to inherit SEO fields.
    """
    
    # Hero Section Fields
    hero_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Main hero title (optional, can also use StreamField hero)"
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
    
    # Author Information
    author_name = models.CharField(
        max_length=100,
        default="Prabuddh Mathur",
        help_text="Author's name"
    )
    author_bio = RichTextField(
        blank=True,
        help_text="Author biography for sidebar display"
    )
    author_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Author profile photo"
    )
    
    # Social Media Links
    website_url = models.URLField(
        blank=True,
        help_text="Personal website URL"
    )
    twitter_url = models.URLField(
        blank=True,
        help_text="Twitter profile URL"
    )
    linkedin_url = models.URLField(
        blank=True,
        help_text="LinkedIn profile URL"
    )
    github_url = models.URLField(
        blank=True,
        help_text="GitHub profile URL"
    )
    email_address = models.EmailField(
        blank=True,
        help_text="Contact email address"
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
        help_text="Number of featured posts to display"
    )
    show_featured_posts = models.BooleanField(
        default=True,
        help_text="Display featured posts section"
    )
    
    # Recent Posts Configuration  
    recent_posts_title = models.CharField(
        max_length=100,
        default="Recent Posts",
        help_text="Title for the recent posts section"
    )
    number_of_recent_posts = models.IntegerField(
        default=5,
        help_text="Number of recent posts to display"
    )
    show_recent_posts = models.BooleanField(
        default=True,
        help_text="Display recent posts section"
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
        ], heading="Hero Section"),
        
        FieldPanel('body'),
        
        MultiFieldPanel([
            FieldPanel('author_name'),
            FieldPanel('author_bio'),
            FieldPanel('author_image'),
        ], heading="Author Information"),
        
        MultiFieldPanel([
            FieldPanel('website_url'),
            FieldPanel('twitter_url'),
            FieldPanel('linkedin_url'),
            FieldPanel('github_url'),
            FieldPanel('email_address'),
        ], heading="Social Media Links"),
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
        """Add extra context for template rendering."""
        context = super().get_context(request)
        
        # Try to import and get blog posts (graceful fallback if blog app doesn't exist)
        try:
            from blog.models import BlogPage
            
            # Get recent posts
            if self.show_recent_posts:
                recent_posts = BlogPage.objects.live().public().order_by('-first_published_at')[:self.number_of_recent_posts]
                context['recent_posts'] = recent_posts
            
            # Get featured posts (assuming there's a featured field on BlogPage)
            if self.show_featured_posts:
                try:
                    featured_posts = BlogPage.objects.live().public().filter(featured=True)[:self.number_of_featured_posts]
                    context['featured_posts'] = featured_posts
                except:
                    # Fallback to recent posts if no featured field exists
                    featured_posts = BlogPage.objects.live().public().order_by('-first_published_at')[:self.number_of_featured_posts]
                    context['featured_posts'] = featured_posts
                    
        except ImportError:
            # Blog app doesn't exist yet, set empty querysets
            context['recent_posts'] = []
            context['featured_posts'] = []
        
        # Add social links for easy template access
        context['social_links'] = {
            'website': self.website_url,
            'twitter': self.twitter_url,
            'linkedin': self.linkedin_url,
            'github': self.github_url,
            'email': self.email_address,
        }
        
        return context
    
    def get_social_links_list(self):
        """Return social links as a list of tuples for template iteration."""
        links = []
        if self.website_url:
            links.append(('website', 'Website', self.website_url, 'fa-globe'))
        if self.twitter_url:
            links.append(('twitter', 'Twitter', self.twitter_url, 'fa-twitter'))
        if self.linkedin_url:
            links.append(('linkedin', 'LinkedIn', self.linkedin_url, 'fa-linkedin'))
        if self.github_url:
            links.append(('github', 'GitHub', self.github_url, 'fa-github'))
        if self.email_address:
            links.append(('email', 'Email', f'mailto:{self.email_address}', 'fa-envelope'))
        return links
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Homepage"
        verbose_name_plural = "Homepages"

