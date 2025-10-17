from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from wagtail import blocks
from wagtail.blocks import RichTextBlock, CharBlock, URLBlock, BooleanBlock
from wagtail.images.blocks import ImageChooserBlock


# =====================================================
# StreamField Blocks
# =====================================================

class TextBlock(blocks.StructBlock):
    """Rich text block with optional alignment and styling."""
    text = RichTextBlock(
        required=True,
        help_text="Rich text content with formatting options"
    )
    alignment = blocks.ChoiceBlock(
        choices=[
            ('left', 'Left'),
            ('center', 'Center'),
            ('right', 'Right'),
            ('justify', 'Justify'),
        ],
        default='left',
        help_text="Text alignment"
    )
    size = blocks.ChoiceBlock(
        choices=[
            ('small', 'Small'),
            ('normal', 'Normal'),
            ('large', 'Large'),
            ('xl', 'Extra Large'),
        ],
        default='normal',
        help_text="Text size"
    )
    
    class Meta:
        icon = 'doc-full'
        label = 'Rich Text'
        template = 'home/blocks/text_block.html'


class ImageBlock(blocks.StructBlock):
    """Image block with caption, alt text, and styling options."""
    image = ImageChooserBlock(
        required=True,
        help_text="Select an image"
    )
    caption = CharBlock(
        required=False,
        max_length=500,
        help_text="Optional image caption"
    )
    alt_text = CharBlock(
        required=True,
        max_length=255,
        help_text="Alternative text for accessibility (required)"
    )
    alignment = blocks.ChoiceBlock(
        choices=[
            ('left', 'Left'),
            ('center', 'Center'),
            ('right', 'Right'),
            ('full', 'Full Width'),
        ],
        default='center',
        help_text="Image alignment"
    )
    size = blocks.ChoiceBlock(
        choices=[
            ('small', 'Small (300px)'),
            ('medium', 'Medium (600px)'),
            ('large', 'Large (900px)'),
            ('full', 'Full Width'),
        ],
        default='medium',
        help_text="Image size"
    )
    rounded = BooleanBlock(
        required=False,
        default=False,
        help_text="Apply rounded corners to the image"
    )
    shadow = BooleanBlock(
        required=False,
        default=False,
        help_text="Add shadow effect to the image"
    )
    
    class Meta:
        icon = 'image'
        label = 'Image'
        template = 'home/blocks/image_block.html'


class HeroBlock(blocks.StructBlock):
    """Hero section block for prominent page headers."""
    title = CharBlock(
        required=True,
        max_length=200,
        help_text="Main hero title"
    )
    subtitle = CharBlock(
        required=False,
        max_length=300,
        help_text="Optional subtitle or description"
    )
    background_image = ImageChooserBlock(
        required=False,
        help_text="Background image for the hero section"
    )
    background_overlay = BooleanBlock(
        required=False,
        default=True,
        help_text="Add dark overlay to improve text readability"
    )
    text_color = blocks.ChoiceBlock(
        choices=[
            ('white', 'White'),
            ('black', 'Black'),
            ('primary', 'Primary Color'),
        ],
        default='white',
        help_text="Text color"
    )
    height = blocks.ChoiceBlock(
        choices=[
            ('small', 'Small (300px)'),
            ('medium', 'Medium (500px)'),
            ('large', 'Large (700px)'),
            ('full', 'Full Screen'),
        ],
        default='medium',
        help_text="Hero section height"
    )
    cta_text = CharBlock(
        required=False,
        max_length=50,
        help_text="Call-to-action button text"
    )
    cta_link = URLBlock(
        required=False,
        help_text="Call-to-action button link"
    )
    cta_style = blocks.ChoiceBlock(
        choices=[
            ('primary', 'Primary Button'),
            ('secondary', 'Secondary Button'),
            ('outline', 'Outline Button'),
        ],
        default='primary',
        help_text="Button style"
    )
    
    class Meta:
        icon = 'view'
        label = 'Hero Section'
        template = 'home/blocks/hero_block.html'


class CallToActionBlock(blocks.StructBlock):
    """Call-to-action block for engagement."""
    title = CharBlock(
        required=True,
        max_length=100,
        help_text="CTA title"
    )
    description = CharBlock(
        required=False,
        max_length=300,
        help_text="Optional description text"
    )
    button_text = CharBlock(
        required=True,
        max_length=50,
        help_text="Button text"
    )
    button_link = URLBlock(
        required=True,
        help_text="Button link URL"
    )
    button_style = blocks.ChoiceBlock(
        choices=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('accent', 'Accent'),
            ('ghost', 'Ghost'),
            ('outline', 'Outline'),
        ],
        default='primary',
        help_text="Button style"
    )
    background_color = blocks.ChoiceBlock(
        choices=[
            ('transparent', 'Transparent'),
            ('base-100', 'Light'),
            ('base-200', 'Light Gray'),
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('accent', 'Accent'),
        ],
        default='base-100',
        help_text="Background color"
    )
    text_alignment = blocks.ChoiceBlock(
        choices=[
            ('left', 'Left'),
            ('center', 'Center'),
            ('right', 'Right'),
        ],
        default='center',
        help_text="Text alignment"
    )
    
    class Meta:
        icon = 'plus-inverse'
        label = 'Call to Action'
        template = 'home/blocks/cta_block.html'


class AuthorBioBlock(blocks.StructBlock):
    """Author biography block for sidebar content."""
    author_name = CharBlock(
        required=True,
        max_length=100,
        help_text="Author's name"
    )
    author_image = ImageChooserBlock(
        required=False,
        help_text="Author's profile photo"
    )
    bio_text = RichTextBlock(
        required=True,
        help_text="Author biography text"
    )
    website_url = URLBlock(
        required=False,
        help_text="Author's website URL"
    )
    twitter_url = URLBlock(
        required=False,
        help_text="Twitter profile URL"
    )
    linkedin_url = URLBlock(
        required=False,
        help_text="LinkedIn profile URL"
    )
    github_url = URLBlock(
        required=False,
        help_text="GitHub profile URL"
    )
    email = blocks.EmailBlock(
        required=False,
        help_text="Contact email address"
    )
    show_social_icons = BooleanBlock(
        required=False,
        default=True,
        help_text="Display social media icons"
    )
    
    class Meta:
        icon = 'user'
        label = 'Author Bio'
        template = 'home/blocks/author_bio_block.html'


class RecentPostsBlock(blocks.StructBlock):
    """Block to display recent blog posts."""
    title = CharBlock(
        required=True,
        default="Recent Posts",
        max_length=100,
        help_text="Section title"
    )
    number_of_posts = blocks.IntegerBlock(
        required=True,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Number of posts to display"
    )
    show_excerpt = BooleanBlock(
        required=False,
        default=True,
        help_text="Show post excerpts"
    )
    show_date = BooleanBlock(
        required=False,
        default=True,
        help_text="Show publication dates"
    )
    show_author = BooleanBlock(
        required=False,
        default=True,
        help_text="Show post authors"
    )
    show_featured_image = BooleanBlock(
        required=False,
        default=True,
        help_text="Show featured images"
    )
    layout_style = blocks.ChoiceBlock(
        choices=[
            ('list', 'List View'),
            ('grid', 'Grid View'),
            ('cards', 'Card View'),
        ],
        default='cards',
        help_text="Display layout"
    )
    
    class Meta:
        icon = 'list-ul'
        label = 'Recent Posts'
        template = 'home/blocks/recent_posts_block.html'


class QuoteBlock(blocks.StructBlock):
    """Blockquote with attribution."""
    quote = CharBlock(
        required=True,
        help_text="Quote text"
    )
    author = CharBlock(
        required=False,
        max_length=100,
        help_text="Quote author"
    )
    author_title = CharBlock(
        required=False,
        max_length=100,
        help_text="Author's title or position"
    )
    style = blocks.ChoiceBlock(
        choices=[
            ('default', 'Default'),
            ('large', 'Large Quote'),
            ('bordered', 'Bordered'),
            ('accent', 'Accent Style'),
        ],
        default='default',
        help_text="Quote style"
    )
    
    class Meta:
        icon = 'openquote'
        label = 'Quote'
        template = 'home/blocks/quote_block.html'


class SpacerBlock(blocks.StructBlock):
    """Spacer block for adding vertical spacing."""
    height = blocks.ChoiceBlock(
        choices=[
            ('small', 'Small (1rem)'),
            ('medium', 'Medium (2rem)'),
            ('large', 'Large (4rem)'),
            ('xl', 'Extra Large (6rem)'),
        ],
        default='medium',
        help_text="Spacer height"
    )
    
    class Meta:
        icon = 'horizontalrule'
        label = 'Spacer'
        template = 'home/blocks/spacer_block.html'


# =====================================================
# HomePage Model
# =====================================================

class HomePage(Page):
    """
    Production-grade Wagtail homepage with extensive StreamField usage.
    Designed for a personal blog with flexible content blocks.
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
    
    # Main Content StreamField
    body = StreamField(
        [
            ('text', TextBlock()),
            ('image', ImageBlock()),
            ('hero', HeroBlock()),
            ('cta', CallToActionBlock()),
            ('author_bio', AuthorBioBlock()),
            ('recent_posts', RecentPostsBlock()),
            ('quote', QuoteBlock()),
            ('spacer', SpacerBlock()),
        ],
        blank=True,
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
    
    # SEO and Meta Fields
    social_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Image for social media sharing (Open Graph)"
    )
    
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
    content_panels = Page.content_panels + [
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
    
    promote_panels = Page.promote_panels + [
        FieldPanel('social_image'),
    ]
    
    settings_panels = Page.settings_panels + [
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
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Homepage"
        verbose_name_plural = "Homepages"


# =====================================================
# Additional Model Methods for Template Usage
# =====================================================

# Add method to get social links as a list for iteration
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

# Add the method to the HomePage class
HomePage.get_social_links_list = get_social_links_list
