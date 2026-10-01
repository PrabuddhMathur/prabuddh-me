from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from rest_framework import serializers
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.rich_text import get_text_for_indexing
from wagtail.search import index
from wagtail_headless_preview.models import HeadlessMixin

from core.blocks import (
    BaseAuthorBioBlock,
    BaseButtonBlock,
    BaseCallToActionBlock,
    BaseHeadingBlock,
    BaseHeroBlock,
    BaseImageBlock,
    BaseQuoteBlock,
    BaseRecentPostsBlock,
    BaseRichTextBlock,
    BaseSpacerBlock,
)
from core.models import SEOFields
from core.serializers import ImageField, PostLinkField, TagsField

WORDS_PER_MINUTE = 200


def count_words(block, value):
    """Words of visible text in a block value, including nested and rich text blocks."""
    if isinstance(block, blocks.RichTextBlock):
        return len(get_text_for_indexing(value.source).split()) if value else 0
    if isinstance(block, (blocks.CharBlock, blocks.TextBlock)):
        return len((value or "").split())
    if isinstance(block, blocks.StructBlock):
        return sum(
            count_words(child, value.get(name)) for name, child in block.child_blocks.items()
        )
    if isinstance(block, blocks.StreamBlock):
        return sum(count_words(child.block, child.value) for child in value)
    if isinstance(block, blocks.ListBlock):
        return sum(count_words(block.child_block, item) for item in value)
    # Choices, URLs, images, numbers and switches aren't read.
    return 0


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey("BlogPage", related_name="tagged_items", on_delete=models.CASCADE)


class BlogPage(HeadlessMixin, SEOFields, Page):
    """A blog post. Its public URL is /YYYY/MM/DD/slug/, from the post date."""

    date = models.DateField(
        "Post date",
        default=timezone.localdate,
        help_text="Publication date for the blog post",
        db_index=True,
    )
    intro = models.CharField(
        max_length=250,
        blank=True,
        help_text="Brief introduction/excerpt (250 characters max)",
    )
    featured_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Featured image displayed in listings and at top of post",
    )
    featured_image_caption = models.CharField(
        max_length=250,
        blank=True,
        help_text="Optional caption for the featured image",
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
            ("recent_posts", BaseRecentPostsBlock()),
        ],
        blank=True,
    )
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    featured = models.BooleanField(
        default=False,
        help_text="Mark as featured post (shown prominently on blog index)",
        db_index=True,
    )
    estimated_reading_time = models.IntegerField(
        default=0,
        editable=False,
        help_text="Estimated reading time in minutes (auto-calculated on save)",
    )
    line_height = models.CharField(
        max_length=20,
        default="default",
        choices=[
            ("default", "Default (1.75)"),
            ("normal", "Normal (1.5)"),
            ("comfortable", "Comfortable (1.55)"),
            ("relaxed", "Relaxed (1.625)"),
            ("spacious", "Spacious (1.8)"),
            ("loose", "Loose (2.0)"),
        ],
        help_text="Line height for blog post content",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.FilterField("date"),
        index.FilterField("featured"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("date")], heading="Post Metadata"),
        FieldPanel("intro"),
        MultiFieldPanel(
            [FieldPanel("featured_image"), FieldPanel("featured_image_caption")],
            heading="Featured Image",
        ),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]
    promote_panels = SEOFields.seo_panels + Page.promote_panels
    settings_panels = Page.settings_panels + [
        MultiFieldPanel([FieldPanel("featured")], heading="Display Options"),
        MultiFieldPanel([FieldPanel("line_height")], heading="Typography"),
    ]
    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(promote_panels, heading="Promote"),
            ObjectList(settings_panels, heading="Settings"),
        ]
    )

    api_fields = [
        APIField("date"),
        APIField("url", serializer=serializers.CharField(source="get_date_url")),
        APIField("intro"),
        APIField("featured"),
        APIField("estimated_reading_time"),
        APIField("line_height"),
        APIField(
            "featured_image",
            serializer=ImageField(
                {"display": "width-1200", "full": "width-2400", "og": "fill-1200x630"}
            ),
        ),
        APIField("featured_image_caption"),
        APIField("body"),
        APIField("tags", serializer=TagsField(source="*")),
        APIField("previous_post", serializer=PostLinkField(source="get_previous_post")),
        APIField("next_post", serializer=PostLinkField(source="get_next_post")),
        *SEOFields.seo_api_fields,
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ["-first_published_at", "-date"]

    @classmethod
    def live_posts(cls):
        """Published posts that anyone can see, with what a post summary shows preloaded."""
        return (
            cls.objects.live()
            .public()
            .select_related("featured_image")
            .prefetch_related("tagged_items__tag", "featured_image__renditions")
        )

    def get_date_url(self):
        """The post's public path: /YYYY/MM/DD/slug/"""
        return f"/{self.date.year:04d}/{self.date.month:02d}/{self.date.day:02d}/{self.slug}/"

    def get_url_parts(self, request=None):
        # Use the date URL everywhere Wagtail builds this page's URL, e.g. the admin's
        # "View live" and the headless redirect to the frontend.
        url_parts = super().get_url_parts(request)
        if url_parts is None:
            return None
        site_id, root_url, _ = url_parts
        return (site_id, root_url, self.get_date_url())

    def get_reading_time(self):
        """Minutes to read the intro and body at 200 words per minute, at least 1."""
        words = len(self.intro.split()) + count_words(self.body.stream_block, self.body)
        return max(1, round(words / WORDS_PER_MINUTE))

    def save(self, *args, **kwargs):
        self.estimated_reading_time = self.get_reading_time()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.date and self.date > timezone.localdate():
            raise ValidationError(
                {"date": ValidationError("Post date cannot be in the future.", code="future_date")}
            )

    def _get_neighbours(self):
        """(older post, newer post) in the list of live posts, newest first."""
        if not hasattr(self, "_neighbours"):
            ids = list(
                BlogPage.live_posts()
                .order_by("-first_published_at", "-id")
                .values_list("id", flat=True)
            )
            older = newer = None
            if self.id in ids:
                index_ = ids.index(self.id)
                if index_ + 1 < len(ids):
                    older = BlogPage.objects.get(id=ids[index_ + 1])
                if index_ > 0:
                    newer = BlogPage.objects.get(id=ids[index_ - 1])
            self._neighbours = (older, newer)
        return self._neighbours

    def get_previous_post(self):
        return self._get_neighbours()[0]

    def get_next_post(self):
        return self._get_neighbours()[1]
