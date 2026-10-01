from django.core.exceptions import ValidationError
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail_headless_preview.models import HeadlessMixin

from blog.models import BlogPage
from core.blocks import (
    BaseAuthorBioBlock,
    BaseCallToActionBlock,
    BaseHeroBlock,
    BaseImageBlock,
    BaseQuoteBlock,
    BaseRecentPostsBlock,
    BaseRichTextBlock,
    BaseSpacerBlock,
)
from core.models import SEOFields
from core.serializers import ImageField, PostSummariesField


class HomePage(HeadlessMixin, SEOFields, Page):
    """The site's home page: a hero, optional blocks, and featured and recent posts."""

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]

    hero_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Main hero title (optional, can also use StreamField hero)",
    )
    hero_subtitle = models.CharField(
        max_length=300,
        blank=True,
        help_text="Hero subtitle or tagline",
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Hero background image",
    )
    hero_cta_text = models.CharField(
        max_length=50,
        blank=True,
        help_text="Call-to-action button text",
    )
    hero_cta_link = models.URLField(
        blank=True,
        help_text="Call-to-action button link",
    )
    hero_text_horizontal = models.CharField(
        max_length=20,
        choices=[("left", "Left"), ("center", "Center"), ("right", "Right")],
        default="left",
        help_text="Horizontal position of hero text",
    )
    hero_text_vertical = models.CharField(
        max_length=20,
        choices=[("top", "Top"), ("center", "Center"), ("bottom", "Bottom")],
        default="center",
        help_text="Vertical position of hero text",
    )
    body = StreamField(
        [
            ("text", BaseRichTextBlock()),
            ("image", BaseImageBlock()),
            ("hero", BaseHeroBlock()),
            ("cta", BaseCallToActionBlock()),
            ("author_bio", BaseAuthorBioBlock()),
            ("recent_posts", BaseRecentPostsBlock()),
            ("quote", BaseQuoteBlock()),
            ("spacer", BaseSpacerBlock()),
        ],
        blank=True,
        help_text="Main page content using flexible blocks",
    )
    featured_posts_title = models.CharField(
        max_length=100,
        default="Featured Posts",
        help_text="Title for the featured posts section",
    )
    number_of_featured_posts = models.IntegerField(
        default=3,
        help_text="Number of featured posts to display",
    )
    show_featured_posts = models.BooleanField(
        default=True,
        help_text="Display featured posts section",
    )
    recent_posts_title = models.CharField(
        max_length=100,
        default="Recent Posts",
        help_text="Title for the recent posts section",
    )
    number_of_recent_posts = models.IntegerField(
        default=5,
        help_text="Number of recent posts to display",
    )
    show_recent_posts = models.BooleanField(
        default=True,
        help_text="Display recent posts section",
    )
    show_author_sidebar = models.BooleanField(
        default=True,
        help_text="Display author information in sidebar",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_subtitle"),
                FieldPanel("hero_image"),
                FieldPanel("hero_cta_text"),
                FieldPanel("hero_cta_link"),
                FieldPanel("hero_text_horizontal"),
                FieldPanel("hero_text_vertical"),
            ],
            heading="Hero Section",
        ),
        FieldPanel("body"),
    ]
    promote_panels = Page.promote_panels + SEOFields.seo_panels
    settings_panels = Page.settings_panels + [
        MultiFieldPanel(
            [
                FieldPanel("featured_posts_title"),
                FieldPanel("number_of_featured_posts"),
                FieldPanel("show_featured_posts"),
            ],
            heading="Featured Posts Settings",
        ),
        MultiFieldPanel(
            [
                FieldPanel("recent_posts_title"),
                FieldPanel("number_of_recent_posts"),
                FieldPanel("show_recent_posts"),
            ],
            heading="Recent Posts Settings",
        ),
        MultiFieldPanel([FieldPanel("show_author_sidebar")], heading="Display Settings"),
    ]
    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(promote_panels, heading="SEO"),
            ObjectList(settings_panels, heading="Settings"),
        ]
    )

    api_fields = [
        APIField("hero_title"),
        APIField("hero_subtitle"),
        APIField(
            "hero_image",
            serializer=ImageField({"hero": "fill-1920x800", "og": "fill-1200x630"}),
        ),
        APIField("hero_cta_text"),
        APIField("hero_cta_link"),
        APIField("hero_text_horizontal"),
        APIField("hero_text_vertical"),
        APIField("body"),
        APIField("show_featured_posts"),
        APIField("featured_posts_title"),
        APIField("featured_posts", serializer=PostSummariesField(source="get_featured_posts")),
        APIField("show_recent_posts"),
        APIField("recent_posts_title"),
        APIField("recent_posts", serializer=PostSummariesField(source="get_recent_posts")),
        APIField("show_author_sidebar"),
        *SEOFields.seo_api_fields,
    ]

    class Meta:
        verbose_name = "Homepage"
        verbose_name_plural = "Homepages"

    def get_featured_posts(self):
        if not self.show_featured_posts:
            return []
        # Tree order (the order posts were created in), as the old site showed them:
        # its query had no order_by, so Wagtail's default path ordering applied.
        posts = BlogPage.live_posts().filter(featured=True).order_by("path")
        return posts[: self.number_of_featured_posts]

    def get_recent_posts(self):
        if not self.show_recent_posts:
            return []
        return BlogPage.live_posts().order_by("-first_published_at")[: self.number_of_recent_posts]

    def clean(self):
        super().clean()
        if not 0 <= self.number_of_featured_posts <= 20:
            raise ValidationError(
                {"number_of_featured_posts": "Number of featured posts must be between 0 and 20."}
            )
        if not 0 <= self.number_of_recent_posts <= 50:
            raise ValidationError(
                {"number_of_recent_posts": "Number of recent posts must be between 0 and 50."}
            )
        if self.hero_cta_text and not self.hero_cta_link:
            raise ValidationError(
                {"hero_cta_link": "CTA link is required when CTA text is provided."}
            )
        if self.hero_cta_link and not self.hero_cta_text:
            raise ValidationError(
                {
                    "hero_cta_text": "CTA button text is required when CTA link is provided. "
                    "Use meaningful text for screen reader users."
                }
            )
        if self.hero_cta_text and not self.hero_cta_text.strip():
            raise ValidationError(
                {
                    "hero_cta_text": "CTA button text cannot be empty or only whitespace. "
                    "Use meaningful text for screen reader users."
                }
            )
