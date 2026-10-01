"""
Site-wide settings, the shared SEO fields and StaticPage, ported from the old site's
core/models.py. Only the fields the old templates actually displayed are kept.
"""

from django.db import models
from rest_framework import serializers
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.api import APIField
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail_headless_preview.models import HeadlessMixin

from .blocks import (
    BaseAuthorBioBlock,
    BaseButtonBlock,
    BaseCallToActionBlock,
    BaseHeadingBlock,
    BaseHeroBlock,
    BaseImageBlock,
    BaseQuoteBlock,
    BaseRichTextBlock,
    BaseSpacerBlock,
    LinkBlock,
)
from .serializers import ImageField

# Page fields


class SEOFields(models.Model):
    """SEO and Open Graph fields shared by every page type (the old BasePage)."""

    meta_description = models.TextField(
        blank=True,
        max_length=160,
        help_text="Meta description for SEO (160 characters max)",
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords for SEO",
    )
    og_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Open Graph title (for social media sharing)",
    )
    og_description = models.TextField(
        blank=True,
        max_length=160,
        help_text="Open Graph description",
    )
    og_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Open Graph image for social media sharing",
    )

    seo_panels = [
        MultiFieldPanel(
            [FieldPanel("meta_description"), FieldPanel("meta_keywords")],
            heading="SEO Meta Tags",
        ),
        MultiFieldPanel(
            [FieldPanel("og_title"), FieldPanel("og_description"), FieldPanel("og_image")],
            heading="Social Media (Open Graph)",
        ),
    ]

    seo_api_fields = [
        APIField("meta_description"),
        APIField("meta_keywords"),
        APIField("og_title"),
        APIField("og_description"),
        APIField("og_image", serializer=ImageField({"og": "fill-1200x630"})),
    ]

    class Meta:
        abstract = True


class StaticPage(HeadlessMixin, SEOFields, Page):
    """About, Contact, Privacy and similar pages."""

    intro = models.TextField(
        blank=True,
        max_length=500,
        help_text="Optional introduction text (500 characters max)",
    )
    body = StreamField(
        [
            ("heading", BaseHeadingBlock()),
            ("text", BaseRichTextBlock()),
            ("image", BaseImageBlock()),
            ("quote", BaseQuoteBlock()),
            ("button", BaseButtonBlock()),
            ("spacer", BaseSpacerBlock()),
            ("hero", BaseHeroBlock()),
            ("cta", BaseCallToActionBlock()),
            ("author_bio", BaseAuthorBioBlock()),
        ],
        blank=True,
        help_text="Main page content using flexible blocks",
    )
    show_last_updated = models.BooleanField(
        default=False,
        help_text="Display last updated date at the bottom of the page",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("show_last_updated"),
    ]
    # The old site showed only the SEO panels here, which left no way to edit the slug,
    # SEO title or search description; Wagtail's own promote panels are added back.
    promote_panels = SEOFields.seo_panels + Page.promote_panels
    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(promote_panels, heading="SEO & Promotion"),
            ObjectList(Page.settings_panels, heading="Settings"),
        ]
    )

    api_fields = [
        APIField("intro"),
        APIField("body"),
        APIField("show_last_updated"),
        APIField("last_updated", serializer=serializers.DateTimeField(source="get_last_updated")),
        *SEOFields.seo_api_fields,
    ]

    class Meta:
        verbose_name = "Static Page"
        verbose_name_plural = "Static Pages"

    def __str__(self):
        return self.title

    def get_last_updated(self):
        return self.last_published_at or self.latest_revision_created_at


# Site settings (Settings menu in the admin)


@register_setting
class SiteSettings(BaseSiteSetting):
    site_name = models.CharField(
        max_length=255,
        default="My Site",
        help_text="Name of the site",
    )
    default_meta_description = models.TextField(
        blank=True,
        max_length=160,
        help_text="Default meta description for pages (160 characters max)",
    )
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Google Analytics tracking ID (e.g., G-XXXXXXXXXX)",
    )

    panels = [
        MultiFieldPanel([FieldPanel("site_name")], heading="Site Information"),
        MultiFieldPanel(
            [FieldPanel("default_meta_description"), FieldPanel("google_analytics_id")],
            heading="SEO Settings",
        ),
    ]

    class Meta:
        verbose_name = "Site Settings"

    def __str__(self):
        return f"Site Settings for {self.site_name}"


def default_navigation():
    return [
        ("link", {"text": "Home", "url": "/"}),
        ("link", {"text": "Blog", "url": "/blog/"}),
        ("link", {"text": "About", "url": "/about/"}),
        ("link", {"text": "Contact", "url": "/contact/"}),
    ]


def default_footer_links():
    return [
        ("link", {"text": "About", "url": "/about/"}),
        ("link", {"text": "Contact", "url": "/contact/"}),
        ("link", {"text": "Privacy", "url": "/privacy/"}),
        ("link", {"text": "Terms", "url": "/terms/"}),
    ]


def links_as_list(stream):
    """A StreamField of LinkBlocks as [{"text", "url"}], skipping incomplete links."""
    return [
        {"text": block.value["text"], "url": block.value["url"]}
        for block in stream
        if block.value["text"] and block.value["url"]
    ]


@register_setting
class HeaderSettings(BaseSiteSetting):
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Site logo (optional, will use site name if not provided)",
    )
    site_title = models.CharField(
        max_length=100,
        default="My Site",
        help_text="Site title displayed in header",
    )
    show_logo = models.BooleanField(
        default=False,
        help_text="Show logo image instead of text title",
    )
    # Replaces the old site's five fixed pairs of nav_link_N_text/url fields.
    navigation = StreamField(
        [("link", LinkBlock())],
        blank=True,
        default=default_navigation,
        help_text="Links in the header, in order",
    )
    show_search = models.BooleanField(
        default=True,
        help_text="Display search bar in header",
    )
    show_theme_toggle = models.BooleanField(
        default=True,
        help_text="Display theme toggle button",
    )
    header_style = models.CharField(
        max_length=20,
        choices=[
            ("sticky", "Sticky (stays at top)"),
            ("static", "Static (scrolls with page)"),
        ],
        default="sticky",
        help_text="Header positioning",
    )

    panels = [
        MultiFieldPanel(
            [FieldPanel("logo"), FieldPanel("site_title"), FieldPanel("show_logo")],
            heading="Branding",
        ),
        MultiFieldPanel([FieldPanel("navigation")], heading="Navigation"),
        MultiFieldPanel(
            [
                FieldPanel("show_search"),
                FieldPanel("show_theme_toggle"),
                FieldPanel("header_style"),
            ],
            heading="Features & Styling",
        ),
    ]

    class Meta:
        verbose_name = "Header Settings"

    def __str__(self):
        return f"Header Settings - {self.site_title}"


@register_setting
class FooterSettings(BaseSiteSetting):
    copyright_text = models.CharField(
        max_length=200,
        default="All rights reserved.",
        help_text="Copyright text displayed in footer",
    )
    show_year = models.BooleanField(
        default=True,
        help_text="Automatically display current year before copyright text",
    )
    # Replaces the old site's four fixed pairs of footer_link_N_text/url fields.
    links = StreamField(
        [("link", LinkBlock())],
        blank=True,
        default=default_footer_links,
        help_text="Quick links in the footer, in order",
    )
    show_newsletter = models.BooleanField(
        default=True,
        help_text="Display newsletter signup section",
    )
    show_quick_links = models.BooleanField(
        default=True,
        help_text="Display quick links section",
    )

    panels = [
        MultiFieldPanel(
            [FieldPanel("copyright_text"), FieldPanel("show_year")], heading="Footer Text"
        ),
        MultiFieldPanel([FieldPanel("links")], heading="Footer Links"),
        MultiFieldPanel(
            [FieldPanel("show_newsletter"), FieldPanel("show_quick_links")],
            heading="Section Visibility",
        ),
    ]

    class Meta:
        verbose_name = "Footer Settings"

    def __str__(self):
        return f"Footer Settings - {self.copyright_text[:50]}"


@register_setting
class AuthorSettings(BaseSiteSetting):
    author_name = models.CharField(
        max_length=100,
        default="Prabuddh Mathur",
        help_text="Your name as it appears on the site",
    )
    author_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Your professional title or tagline (e.g., 'Software Engineer & Writer')",
    )
    author_bio_short = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short bio for sidebars and cards (200 characters max)",
    )
    author_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Profile photo",
    )
    email_address = models.EmailField(blank=True, help_text="Contact email address")
    website_url = models.URLField(blank=True, help_text="Personal website URL")
    twitter_url = models.URLField(blank=True, help_text="Twitter/X profile URL")
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    github_url = models.URLField(blank=True, help_text="GitHub profile URL")
    mastodon_url = models.URLField(blank=True, help_text="Mastodon profile URL")

    panels = [
        MultiFieldPanel(
            [FieldPanel("author_name"), FieldPanel("author_title"), FieldPanel("author_image")],
            heading="Author Identity",
        ),
        MultiFieldPanel([FieldPanel("author_bio_short")], heading="Biography"),
        MultiFieldPanel(
            [
                FieldPanel("email_address"),
                FieldPanel("website_url"),
                FieldPanel("twitter_url"),
                FieldPanel("linkedin_url"),
                FieldPanel("github_url"),
                FieldPanel("mastodon_url"),
            ],
            heading="Contact & Social Links",
        ),
    ]

    class Meta:
        verbose_name = "Author Settings"

    def __str__(self):
        return f"Author: {self.author_name}"

    def get_social_links(self):
        """The non-empty social links, in the order the old site showed them."""
        links = [
            ("Website", self.website_url, "globe"),
            ("Twitter", self.twitter_url, "twitter"),
            ("LinkedIn", self.linkedin_url, "linkedin"),
            ("GitHub", self.github_url, "github"),
            ("Mastodon", self.mastodon_url, "mastodon"),
            ("Email", self.email_address and f"mailto:{self.email_address}", "email"),
        ]
        return [{"name": name, "url": url, "icon": icon} for name, url, icon in links if url]
