from django.db import models
from django.core.exceptions import ValidationError
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail import blocks
from wagtail.blocks import RichTextBlock, CharBlock, URLBlock, BooleanBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.search import index


# =====================================================
# Base StreamField Blocks (Reusable across apps)
# =====================================================

class BaseHeadingBlock(blocks.StructBlock):
    """Reusable heading block with configurable level and styling."""
    heading_text = CharBlock(
        required=True,
        max_length=255,
        help_text="Enter the heading text"
    )
    heading_level = blocks.ChoiceBlock(
        choices=[
            ('h1', 'Heading 1'),
            ('h2', 'Heading 2'),
            ('h3', 'Heading 3'),
            ('h4', 'Heading 4'),
            ('h5', 'Heading 5'),
            ('h6', 'Heading 6'),
        ],
        default='h2',
        help_text="Select heading level"
    )
    alignment = blocks.ChoiceBlock(
        choices=[
            ('left', 'Left'),
            ('center', 'Center'),
            ('right', 'Right'),
        ],
        default='left',
        help_text="Text alignment"
    )
    
    class Meta:
        icon = 'title'
        label = 'Heading'
        template = 'core/blocks/heading_block.html'


class BaseRichTextBlock(blocks.StructBlock):
    """Reusable rich text block with alignment options."""
    text = RichTextBlock(
        required=True,
        help_text="Rich text content with formatting options",
        features=['bold', 'italic', 'link', 'ol', 'ul', 'h2', 'h3', 'h4', 'hr', 'spoiler']
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
    
    class Meta:
        icon = 'doc-full'
        label = 'Rich Text'
        template = 'core/blocks/rich_text_block.html'


class BaseImageBlock(blocks.StructBlock):
    """Reusable image block with caption and alignment."""
    image = ImageChooserBlock(
        required=True,
        help_text="Select an image"
    )
    caption = CharBlock(
        required=False,
        max_length=255,
        help_text="Optional image caption"
    )
    alt_text = CharBlock(
        required=False,
        max_length=255,
        help_text="Alternative text for accessibility (recommended)"
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
    
    class Meta:
        icon = 'image'
        label = 'Image'
        template = 'core/blocks/image_block.html'


class BaseButtonBlock(blocks.StructBlock):
    """Reusable button block with styling options and accessibility validation."""
    button_text = CharBlock(
        required=True,
        max_length=50,
        help_text="Button text (required for accessibility)"
    )
    button_url = URLBlock(
        required=True,
        help_text="Button URL"
    )
    button_style = blocks.ChoiceBlock(
        choices=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('accent', 'Accent'),
            ('ghost', 'Ghost'),
            ('link', 'Link'),
        ],
        default='primary',
        help_text="Button style (DaisyUI)"
    )
    button_size = blocks.ChoiceBlock(
        choices=[
            ('xs', 'Extra Small'),
            ('sm', 'Small'),
            ('md', 'Medium'),
            ('lg', 'Large'),
        ],
        default='md',
        help_text="Button size"
    )
    open_in_new_tab = BooleanBlock(
        required=False,
        default=False,
        help_text="Open link in new tab"
    )
    
    def clean(self, value):
        """Validate button has meaningful text for accessibility."""
        errors = {}
        
        if not value.get('button_text') or not value.get('button_text').strip():
            errors['button_text'] = ValidationError(
                'Button text is required and cannot be empty. Use meaningful text for screen reader users.'
            )
        
        if errors:
            raise ValidationError('Validation error in button block', params=errors)
        
        return super().clean(value)
    
    class Meta:
        icon = 'link'
        label = 'Button'
        template = 'core/blocks/button_block.html'

# To remove later if not used. [29/12/2025]
class BaseSpacerBlock(blocks.StructBlock):
    """Reusable spacer block for adding vertical space."""
    height = blocks.ChoiceBlock(
        choices=[
            ('small', 'Small (1rem)'),
            ('medium', 'Medium (2rem)'),
            ('large', 'Large (4rem)'),
            ('xlarge', 'Extra Large (6rem)'),
        ],
        default='medium',
        help_text="Spacer height"
    )
    
    class Meta:
        icon = 'arrows-up-down'
        label = 'Spacer'
        template = 'core/blocks/spacer_block.html'


class BaseHeroBlock(blocks.StructBlock):
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
    
    def clean(self, value):
        """Validate hero CTA button text for accessibility."""
        errors = {}
        
        # If CTA link is provided, text must also be provided
        if value.get('cta_link') and not value.get('cta_text'):
            errors['cta_text'] = ValidationError(
                'CTA button text is required when CTA link is provided. Use meaningful text for screen reader users.'
            )
        
        # If CTA text is provided but empty/whitespace
        if value.get('cta_text') and not value.get('cta_text').strip():
            errors['cta_text'] = ValidationError(
                'CTA button text cannot be empty or only whitespace. Use meaningful text for screen reader users.'
            )
        
        # If CTA text is provided, link must also be provided
        if value.get('cta_text') and not value.get('cta_link'):
            errors['cta_link'] = ValidationError(
                'CTA link is required when CTA button text is provided.'
            )
        
        if errors:
            raise ValidationError('Validation error in Hero block', params=errors)
        
        return super().clean(value)
    
    class Meta:
        icon = 'view'
        label = 'Hero Section'
        template = 'core/blocks/hero_block.html'


class BaseCallToActionBlock(blocks.StructBlock):
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
    
    def clean(self, value):
        """Validate CTA button has meaningful text for accessibility."""
        errors = {}
        
        if not value.get('button_text') or not value.get('button_text').strip():
            errors['button_text'] = ValidationError(
                'Button text is required and cannot be empty. Use meaningful text for screen reader users.'
            )
        
        if errors:
            raise ValidationError('Validation error in CTA block', params=errors)
        
        return super().clean(value)
    
    class Meta:
        icon = 'plus-inverse'
        label = 'Call to Action'
        template = 'core/blocks/cta_block.html'


class BaseAuthorBioBlock(blocks.StructBlock):
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
        template = 'core/blocks/author_bio_block.html'


class BaseRecentPostsBlock(blocks.StructBlock):
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
        template = 'core/blocks/recent_posts_block.html'


class BaseQuoteBlock(blocks.StructBlock):
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
        template = 'core/blocks/quote_block.html'


# =====================================================
# Base Site Settings (Global configuration)
# =====================================================

@register_setting
class SiteSettings(BaseSiteSetting):
    """Global site settings accessible throughout the site."""
    
    site_name = models.CharField(
        max_length=255,
        default="My Site",
        help_text="Name of the site",
        db_index=True,
    )
    
    tagline = models.CharField(
        max_length=255,
        blank=True,
        help_text="Site tagline or slogan"
    )
    
    site_description = models.TextField(
        blank=True,
        help_text="Brief description of the site (for SEO)"
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        help_text="Contact email address"
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )
    
    # Social Media Links
    twitter_url = models.URLField(
        blank=True,
        help_text="Twitter/X profile URL"
    )
    
    linkedin_url = models.URLField(
        blank=True,
        help_text="LinkedIn profile URL"
    )
    
    github_url = models.URLField(
        blank=True,
        help_text="GitHub profile URL"
    )
    
    facebook_url = models.URLField(
        blank=True,
        help_text="Facebook profile URL"
    )
    
    instagram_url = models.URLField(
        blank=True,
        help_text="Instagram profile URL"
    )
    
    # SEO Settings
    default_meta_description = models.TextField(
        blank=True,
        max_length=160,
        help_text="Default meta description for pages (160 characters max)"
    )
    
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Google Analytics tracking ID (e.g., G-XXXXXXXXXX)"
    )
    
    # Footer Settings
    footer_text = models.TextField(
        blank=True,
        help_text="Text to display in the footer"
    )
    
    copyright_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Copyright text"
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel('site_name'),
            FieldPanel('tagline'),
            FieldPanel('site_description'),
        ], heading="Site Information"),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('contact_phone'),
        ], heading="Contact Information"),
        
        MultiFieldPanel([
            FieldPanel('twitter_url'),
            FieldPanel('linkedin_url'),
            FieldPanel('github_url'),
            FieldPanel('facebook_url'),
            FieldPanel('instagram_url'),
        ], heading="Social Media Links"),
        
        MultiFieldPanel([
            FieldPanel('default_meta_description'),
            FieldPanel('google_analytics_id'),
        ], heading="SEO Settings"),
        
        MultiFieldPanel([
            FieldPanel('footer_text'),
            FieldPanel('copyright_text'),
        ], heading="Footer Settings"),
    ]
    
    class Meta:
        verbose_name = 'Site Settings'
    
    def __str__(self):
        """String representation of SiteSettings."""
        return f"Site Settings for {self.site_name}"


# =====================================================
# Base Abstract Models (for inheritance)
# =====================================================

class BasePage(Page):
    """Abstract base page model with common fields for all pages."""
    
    # SEO Fields
    meta_description = models.TextField(
        blank=True,
        max_length=160,
        help_text="Meta description for SEO (160 characters max)"
    )
    
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords for SEO",
        db_index=True,
    )
    
    # Social sharing fields
    og_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Open Graph title (for social media sharing)"
    )
    
    og_description = models.TextField(
        blank=True,
        max_length=160,
        help_text="Open Graph description"
    )
    
    og_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Open Graph image for social media sharing"
    )
    
    # Display settings
    show_in_menus_default = True
    
    # Common panels for SEO
    seo_panels = [
        MultiFieldPanel([
            FieldPanel('meta_description'),
            FieldPanel('meta_keywords'),
        ], heading="SEO Meta Tags"),
        
        MultiFieldPanel([
            FieldPanel('og_title'),
            FieldPanel('og_description'),
            FieldPanel('og_image'),
        ], heading="Social Media (Open Graph)"),
    ]
    
    class Meta:
        abstract = True


# =====================================================
# Header and Footer Settings
# =====================================================

@register_setting
class HeaderSettings(BaseSiteSetting):
    """
    Site-wide header/navigation settings.
    Manage from Settings > Header in Wagtail admin.
    """
    
    # Logo and Branding
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Site logo (optional, will use site name if not provided)"
    )
    site_title = models.CharField(
        max_length=100,
        default="My Site",
        help_text="Site title displayed in header"
    )
    show_logo = models.BooleanField(
        default=False,
        help_text="Show logo image instead of text title"
    )
    
    # Navigation Links
    nav_link_1_text = models.CharField(
        max_length=50,
        default="Home",
        help_text="First navigation link text"
    )
    nav_link_1_url = models.CharField(
        max_length=200,
        default="/",
        help_text="First navigation link URL"
    )
    
    nav_link_2_text = models.CharField(
        max_length=50,
        blank=True,
        default="Blog",
        help_text="Second navigation link text"
    )
    nav_link_2_url = models.CharField(
        max_length=200,
        blank=True,
        default="/blog/",
        help_text="Second navigation link URL"
    )
    
    nav_link_3_text = models.CharField(
        max_length=50,
        blank=True,
        default="About",
        help_text="Third navigation link text"
    )
    nav_link_3_url = models.CharField(
        max_length=200,
        blank=True,
        default="/about/",
        help_text="Third navigation link URL"
    )
    
    nav_link_4_text = models.CharField(
        max_length=50,
        blank=True,
        default="Contact",
        help_text="Fourth navigation link text"
    )
    nav_link_4_url = models.CharField(
        max_length=200,
        blank=True,
        default="/contact/",
        help_text="Fourth navigation link URL"
    )
    
    nav_link_5_text = models.CharField(
        max_length=50,
        blank=True,
        help_text="Fifth navigation link text (optional)"
    )
    nav_link_5_url = models.CharField(
        max_length=200,
        blank=True,
        help_text="Fifth navigation link URL"
    )
    
    # Search and Features
    show_search = models.BooleanField(
        default=True,
        help_text="Display search bar in header"
    )
    show_theme_toggle = models.BooleanField(
        default=True,
        help_text="Display theme toggle button"
    )
    
    # Styling
    header_style = models.CharField(
        max_length=20,
        choices=[
            ('sticky', 'Sticky (stays at top)'),
            ('static', 'Static (scrolls with page)'),
        ],
        default='sticky',
        help_text="Header positioning"
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel('logo'),
            FieldPanel('site_title'),
            FieldPanel('show_logo'),
        ], heading="Branding"),
        
        MultiFieldPanel([
            FieldPanel('nav_link_1_text'),
            FieldPanel('nav_link_1_url'),
        ], heading="Navigation Link 1"),
        
        MultiFieldPanel([
            FieldPanel('nav_link_2_text'),
            FieldPanel('nav_link_2_url'),
        ], heading="Navigation Link 2"),
        
        MultiFieldPanel([
            FieldPanel('nav_link_3_text'),
            FieldPanel('nav_link_3_url'),
        ], heading="Navigation Link 3"),
        
        MultiFieldPanel([
            FieldPanel('nav_link_4_text'),
            FieldPanel('nav_link_4_url'),
        ], heading="Navigation Link 4"),
        
        MultiFieldPanel([
            FieldPanel('nav_link_5_text'),
            FieldPanel('nav_link_5_url'),
        ], heading="Navigation Link 5 (Optional)"),
        
        MultiFieldPanel([
            FieldPanel('show_search'),
            FieldPanel('show_theme_toggle'),
            FieldPanel('header_style'),
        ], heading="Features & Styling"),
    ]
    
    class Meta:
        verbose_name = "Header Settings"
    
    def __str__(self):
        """String representation of HeaderSettings."""
        return f"Header Settings - {self.site_title}"
    
    def get_navigation_links(self):
        """Return a list of navigation links for template iteration."""
        links = []
        if self.nav_link_1_text and self.nav_link_1_url:
            links.append({'text': self.nav_link_1_text, 'url': self.nav_link_1_url})
        if self.nav_link_2_text and self.nav_link_2_url:
            links.append({'text': self.nav_link_2_text, 'url': self.nav_link_2_url})
        if self.nav_link_3_text and self.nav_link_3_url:
            links.append({'text': self.nav_link_3_text, 'url': self.nav_link_3_url})
        if self.nav_link_4_text and self.nav_link_4_url:
            links.append({'text': self.nav_link_4_text, 'url': self.nav_link_4_url})
        if self.nav_link_5_text and self.nav_link_5_url:
            links.append({'text': self.nav_link_5_text, 'url': self.nav_link_5_url})
        return links


@register_setting
class FooterSettings(BaseSiteSetting):
    """
    Site-wide footer settings.
    Manage from Settings > Footer in Wagtail admin.
    """
    
    # Footer Text
    copyright_text = models.CharField(
        max_length=200,
        default="All rights reserved.",
        help_text="Copyright text displayed in footer"
    )
    show_year = models.BooleanField(
        default=True,
        help_text="Automatically display current year before copyright text"
    )
    
    # Footer Links - Column 1
    footer_col1_title = models.CharField(
        max_length=50,
        blank=True,
        default="Quick Links",
        help_text="First column title"
    )
    footer_link_1_text = models.CharField(
        max_length=50,
        blank=True,
        default="About",
        help_text="Footer link text"
    )
    footer_link_1_url = models.CharField(
        max_length=200,
        blank=True,
        default="/about/",
        help_text="Footer link URL"
    )
    footer_link_2_text = models.CharField(
        max_length=50,
        blank=True,
        default="Contact",
        help_text="Footer link text"
    )
    footer_link_2_url = models.CharField(
        max_length=200,
        blank=True,
        default="/contact/",
        help_text="Footer link URL"
    )
    footer_link_3_text = models.CharField(
        max_length=50,
        blank=True,
        default="Privacy",
        help_text="Footer link text"
    )
    footer_link_3_url = models.CharField(
        max_length=200,
        blank=True,
        default="/privacy/",
        help_text="Footer link URL"
    )
    footer_link_4_text = models.CharField(
        max_length=50,
        blank=True,
        default="Terms",
        help_text="Footer link text"
    )
    footer_link_4_url = models.CharField(
        max_length=200,
        blank=True,
        default="/terms/",
        help_text="Footer link URL"
    )
    
    # Section Visibility Toggles
    show_newsletter = models.BooleanField(
        default=True,
        help_text="Display newsletter signup section"
    )
    show_quick_links = models.BooleanField(
        default=True,
        help_text="Display quick links section"
    )
    
    # Additional Info
    footer_description = models.TextField(
        blank=True,
        help_text="Optional footer description or additional information"
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel('copyright_text'),
            FieldPanel('show_year'),
            FieldPanel('footer_description'),
        ], heading="Footer Text"),
        
        MultiFieldPanel([
            FieldPanel('footer_col1_title'),
            FieldPanel('footer_link_1_text'),
            FieldPanel('footer_link_1_url'),
            FieldPanel('footer_link_2_text'),
            FieldPanel('footer_link_2_url'),
            FieldPanel('footer_link_3_text'),
            FieldPanel('footer_link_3_url'),
            FieldPanel('footer_link_4_text'),
            FieldPanel('footer_link_4_url'),
        ], heading="Footer Links"),
        
        MultiFieldPanel([
            FieldPanel('show_newsletter'),
            FieldPanel('show_quick_links'),
        ], heading="Section Visibility"),
    ]
    
    class Meta:
        verbose_name = "Footer Settings"
    
    def __str__(self):
        """String representation of FooterSettings."""
        return f"Footer Settings - {self.copyright_text[:50]}"
    
    def get_footer_links(self):
        """Return a list of footer links for template iteration."""
        links = []
        if self.footer_link_1_text and self.footer_link_1_url:
            links.append({'text': self.footer_link_1_text, 'url': self.footer_link_1_url})
        if self.footer_link_2_text and self.footer_link_2_url:
            links.append({'text': self.footer_link_2_text, 'url': self.footer_link_2_url})
        if self.footer_link_3_text and self.footer_link_3_url:
            links.append({'text': self.footer_link_3_text, 'url': self.footer_link_3_url})
        if self.footer_link_4_text and self.footer_link_4_url:
            links.append({'text': self.footer_link_4_text, 'url': self.footer_link_4_url})
        return links


# =====================================================
# Author Settings (Singleton for Site Author)
# =====================================================

@register_setting
class AuthorSettings(BaseSiteSetting):
    """
    Centralized author information for the site.
    This is a singleton model accessible throughout the site.
    Use this for consistent author information across blog posts, footers, etc.
    """
    
    # Author Identity
    author_name = models.CharField(
        max_length=100,
        default="Prabuddh Mathur",
        help_text="Your name as it appears on the site"
    )
    
    author_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Your professional title or tagline (e.g., 'Software Engineer & Writer')"
    )
    
    author_bio = models.TextField(
        blank=True,
        help_text="Your biography for display on blog posts and author pages"
    )
    
    author_bio_short = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short bio for sidebars and cards (200 characters max)"
    )
    
    # Author Image
    author_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Profile photo"
    )
    
    # Contact & Social Links
    email_address = models.EmailField(
        blank=True,
        help_text="Contact email address"
    )
    
    website_url = models.URLField(
        blank=True,
        help_text="Personal website URL"
    )
    
    twitter_url = models.URLField(
        blank=True,
        help_text="Twitter/X profile URL"
    )
    
    linkedin_url = models.URLField(
        blank=True,
        help_text="LinkedIn profile URL"
    )
    
    github_url = models.URLField(
        blank=True,
        help_text="GitHub profile URL"
    )
    
    mastodon_url = models.URLField(
        blank=True,
        help_text="Mastodon profile URL"
    )
    
    # Display Options
    show_author_in_footer = models.BooleanField(
        default=True,
        help_text="Display author information in the footer"
    )
    
    show_author_on_blog_posts = models.BooleanField(
        default=True,
        help_text="Display author bio at the end of blog posts"
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel('author_name'),
            FieldPanel('author_title'),
            FieldPanel('author_image'),
        ], heading="Author Identity"),
        
        MultiFieldPanel([
            FieldPanel('author_bio'),
            FieldPanel('author_bio_short'),
        ], heading="Biography"),
        
        MultiFieldPanel([
            FieldPanel('email_address'),
            FieldPanel('website_url'),
            FieldPanel('twitter_url'),
            FieldPanel('linkedin_url'),
            FieldPanel('github_url'),
            FieldPanel('mastodon_url'),
        ], heading="Contact & Social Links"),
        
        MultiFieldPanel([
            FieldPanel('show_author_in_footer'),
            FieldPanel('show_author_on_blog_posts'),
        ], heading="Display Options"),
    ]
    
    class Meta:
        verbose_name = 'Author Settings'
    
    def __str__(self):
        return f"Author: {self.author_name}"
    
    def get_social_links(self):
        """Return social links as a list for template iteration."""
        links = []
        if self.website_url:
            links.append({
                'name': 'Website',
                'url': self.website_url,
                'icon': 'globe'
            })
        if self.twitter_url:
            links.append({
                'name': 'Twitter',
                'url': self.twitter_url,
                'icon': 'twitter'
            })
        if self.linkedin_url:
            links.append({
                'name': 'LinkedIn',
                'url': self.linkedin_url,
                'icon': 'linkedin'
            })
        if self.github_url:
            links.append({
                'name': 'GitHub',
                'url': self.github_url,
                'icon': 'github'
            })
        if self.mastodon_url:
            links.append({
                'name': 'Mastodon',
                'url': self.mastodon_url,
                'icon': 'mastodon'
            })
        if self.email_address:
            links.append({
                'name': 'Email',
                'url': f'mailto:{self.email_address}',
                'icon': 'email'
            })
        return links


# =====================================================
# Static Page Model (for About, Contact, Terms, etc.)
# =====================================================

class StaticPage(BasePage):
    """
    Flexible static page model for content like About, Contact, Terms, Privacy, etc.
    Uses StreamField for maximum flexibility in content layout.
    Production-grade with validation and search indexing.
    """
    
    # Page Introduction
    intro = models.TextField(
        blank=True,
        max_length=500,
        help_text="Optional introduction text (500 characters max)"
    )
    
    # Main Content (StreamField with all available blocks)
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
    ], 
    blank=True,
    use_json_field=True,
    help_text="Main page content using flexible blocks"
    )
    
    # Display Settings
    show_last_updated = models.BooleanField(
        default=False,
        help_text="Display last updated date at the bottom of the page"
    )
    
    # Search configuration
    search_fields = BasePage.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]
    
    # Content panels for the editor
    content_panels = BasePage.content_panels + [
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('show_last_updated'),
    ]
    
    # SEO panels from BasePage
    promote_panels = BasePage.seo_panels
    
    # Combine into tabbed interface
    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(promote_panels, heading='SEO & Promotion'),
        ObjectList(BasePage.settings_panels, heading='Settings'),
    ])
    
    class Meta:
        verbose_name = "Static Page"
        verbose_name_plural = "Static Pages"
    
    def __str__(self):
        """String representation of the page."""
        return self.title
    
    def get_context(self, request, *args, **kwargs):
        """Add custom context to the template."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add last modified date if needed
        if self.show_last_updated:
            context['last_updated'] = self.last_published_at or self.latest_revision_created_at
        
        return context
