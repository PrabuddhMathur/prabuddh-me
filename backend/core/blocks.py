"""
StreamField blocks shared by every page type, ported from the old site's core/models.py.

There are no block templates: the frontend renders each block from its API
representation (see APIStructBlock).
"""

from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.rich_text import expand_db_html

from .serializers import serialize_image, serialize_post_summary


class APIStructBlock(blocks.StructBlock):
    """
    A StructBlock whose API representation is what the frontend expects: rich text as
    front-end HTML (internal links expanded to real URLs), images as
    {"id", "title", "renditions"}, and "" rather than null for empty text.
    """

    # Renditions for each image child block: {"child block name": {"name": "filter spec"}}.
    image_renditions = {}

    def get_api_representation(self, value, context=None):
        data = {}
        for name, block in self.child_blocks.items():
            child_value = value.get(name)
            if isinstance(block, ImageChooserBlock):
                data[name] = serialize_image(child_value, self.image_renditions[name])
            elif isinstance(block, blocks.RichTextBlock):
                data[name] = expand_db_html(child_value.source) if child_value else ""
            elif child_value is None and isinstance(
                block, (blocks.CharBlock, blocks.URLBlock, blocks.EmailBlock)
            ):
                data[name] = ""
            else:
                data[name] = block.get_api_representation(child_value, context=context)
        return data


class BaseHeadingBlock(APIStructBlock):
    """Reusable heading block with configurable level and styling."""

    heading_text = blocks.CharBlock(
        required=True,
        max_length=255,
        help_text="Enter the heading text",
    )
    heading_level = blocks.ChoiceBlock(
        choices=[
            ("h1", "Heading 1"),
            ("h2", "Heading 2"),
            ("h3", "Heading 3"),
            ("h4", "Heading 4"),
            ("h5", "Heading 5"),
            ("h6", "Heading 6"),
        ],
        default="h2",
        help_text="Select heading level",
    )
    alignment = blocks.ChoiceBlock(
        choices=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
        ],
        default="left",
        help_text="Text alignment",
    )

    class Meta:
        icon = "title"
        label = "Heading"


class BaseRichTextBlock(APIStructBlock):
    """Reusable rich text block with alignment options."""

    text = blocks.RichTextBlock(
        required=True,
        help_text="Rich text content with formatting options",
        # "spoiler" is registered in core/wagtail_hooks.py.
        features=["bold", "italic", "link", "ol", "ul", "h2", "h3", "h4", "hr", "spoiler"],
    )
    alignment = blocks.ChoiceBlock(
        choices=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
            ("justify", "Justify"),
        ],
        default="left",
        help_text="Text alignment",
    )

    class Meta:
        icon = "doc-full"
        label = "Rich Text"


class BaseImageBlock(APIStructBlock):
    """Reusable image block with caption and alignment."""

    image = ImageChooserBlock(
        required=True,
        help_text="Select an image",
    )
    caption = blocks.CharBlock(
        required=False,
        max_length=255,
        help_text="Optional image caption",
    )
    alt_text = blocks.CharBlock(
        required=False,
        max_length=255,
        help_text="Alternative text for accessibility (recommended)",
    )
    alignment = blocks.ChoiceBlock(
        choices=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
            ("full", "Full Width"),
        ],
        default="center",
        help_text="Image alignment",
    )

    image_renditions = {"image": {"display": "fill-1200x800", "full": "width-2400"}}

    class Meta:
        icon = "image"
        label = "Image"


class BaseButtonBlock(APIStructBlock):
    """Reusable button block with size options and accessibility validation."""

    button_text = blocks.CharBlock(
        required=True,
        max_length=50,
        help_text="Button text (required for accessibility)",
    )
    button_url = blocks.URLBlock(
        required=True,
        help_text="Button URL",
    )
    button_size = blocks.ChoiceBlock(
        choices=[
            ("xs", "Extra Small"),
            ("sm", "Small"),
            ("md", "Medium"),
            ("lg", "Large"),
        ],
        default="md",
        help_text="Button size",
    )
    open_in_new_tab = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Open link in new tab",
    )

    def clean(self, value):
        """Validate button has meaningful text for accessibility."""
        if not (value.get("button_text") or "").strip():
            raise blocks.StructBlockValidationError(
                block_errors={
                    "button_text": ValidationError(
                        "Button text is required and cannot be empty. "
                        "Use meaningful text for screen reader users."
                    )
                }
            )
        return super().clean(value)

    class Meta:
        icon = "link"
        label = "Button"


class BaseSpacerBlock(APIStructBlock):
    """Reusable spacer block for adding vertical space."""

    height = blocks.ChoiceBlock(
        choices=[
            ("small", "Small (1rem)"),
            ("medium", "Medium (2rem)"),
            ("large", "Large (4rem)"),
            ("xlarge", "Extra Large (6rem)"),
        ],
        default="medium",
        help_text="Spacer height",
    )

    class Meta:
        icon = "arrows-up-down"
        label = "Spacer"


class BaseHeroBlock(APIStructBlock):
    """Hero section block for prominent page headers."""

    title = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Main hero title",
    )
    subtitle = blocks.CharBlock(
        required=False,
        max_length=300,
        help_text="Optional subtitle or description",
    )
    background_image = ImageChooserBlock(
        required=False,
        help_text="Background image for the hero section",
    )
    background_overlay = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Add dark overlay to improve text readability",
    )
    height = blocks.ChoiceBlock(
        choices=[
            ("small", "Small (300px)"),
            ("medium", "Medium (500px)"),
            ("large", "Large (700px)"),
            ("full", "Full Screen"),
        ],
        default="medium",
        help_text="Hero section height",
    )
    cta_text = blocks.CharBlock(
        required=False,
        max_length=50,
        help_text="Call-to-action button text",
    )
    cta_link = blocks.URLBlock(
        required=False,
        help_text="Call-to-action button link",
    )

    image_renditions = {"background_image": {"original": "original"}}

    def clean(self, value):
        """Validate hero CTA button text for accessibility."""
        errors = {}
        cta_text = value.get("cta_text")
        cta_link = value.get("cta_link")

        # If CTA link is provided, text must also be provided
        if cta_link and not cta_text:
            errors["cta_text"] = ValidationError(
                "CTA button text is required when CTA link is provided. "
                "Use meaningful text for screen reader users."
            )

        # If CTA text is provided but empty/whitespace
        if cta_text and not cta_text.strip():
            errors["cta_text"] = ValidationError(
                "CTA button text cannot be empty or only whitespace. "
                "Use meaningful text for screen reader users."
            )

        # If CTA text is provided, link must also be provided
        if cta_text and not cta_link:
            errors["cta_link"] = ValidationError(
                "CTA link is required when CTA button text is provided."
            )

        if errors:
            raise blocks.StructBlockValidationError(block_errors=errors)
        return super().clean(value)

    class Meta:
        icon = "view"
        label = "Hero Section"


class BaseCallToActionBlock(APIStructBlock):
    """Call-to-action block for engagement."""

    title = blocks.CharBlock(
        required=True,
        max_length=100,
        help_text="CTA title",
    )
    description = blocks.CharBlock(
        required=False,
        max_length=300,
        help_text="Optional description text",
    )
    button_text = blocks.CharBlock(
        required=True,
        max_length=50,
        help_text="Button text",
    )
    button_link = blocks.URLBlock(
        required=True,
        help_text="Button link URL",
    )
    background_color = blocks.ChoiceBlock(
        choices=[
            ("transparent", "Transparent"),
            ("base-100", "Light"),
            ("base-200", "Light Gray"),
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("accent", "Accent"),
        ],
        default="base-100",
        help_text="Background color",
    )
    text_alignment = blocks.ChoiceBlock(
        choices=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
        ],
        default="center",
        help_text="Text alignment",
    )

    def clean(self, value):
        """Validate CTA button has meaningful text for accessibility."""
        if not (value.get("button_text") or "").strip():
            raise blocks.StructBlockValidationError(
                block_errors={
                    "button_text": ValidationError(
                        "Button text is required and cannot be empty. "
                        "Use meaningful text for screen reader users."
                    )
                }
            )
        return super().clean(value)

    class Meta:
        icon = "plus-inverse"
        label = "Call to Action"


class BaseAuthorBioBlock(APIStructBlock):
    """Author biography block for sidebar content."""

    author_name = blocks.CharBlock(
        required=True,
        max_length=100,
        help_text="Author's name",
    )
    author_image = ImageChooserBlock(
        required=False,
        help_text="Author's profile photo",
    )
    bio_text = blocks.RichTextBlock(
        required=True,
        help_text="Author biography text",
    )
    website_url = blocks.URLBlock(
        required=False,
        help_text="Author's website URL",
    )
    twitter_url = blocks.URLBlock(
        required=False,
        help_text="Twitter profile URL",
    )
    linkedin_url = blocks.URLBlock(
        required=False,
        help_text="LinkedIn profile URL",
    )
    github_url = blocks.URLBlock(
        required=False,
        help_text="GitHub profile URL",
    )
    email = blocks.EmailBlock(
        required=False,
        help_text="Contact email address",
    )
    show_social_icons = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Display social media icons",
    )

    image_renditions = {"author_image": {"avatar": "fill-96x96"}}

    class Meta:
        icon = "user"
        label = "Author Bio"


class BaseRecentPostsBlock(APIStructBlock):
    """Block to display recent blog posts."""

    title = blocks.CharBlock(
        required=True,
        default="Recent Posts",
        max_length=100,
        help_text="Section title",
    )
    number_of_posts = blocks.IntegerBlock(
        required=True,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Number of posts to display",
    )
    show_excerpt = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Show post excerpts",
    )
    show_date = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Show publication dates",
    )
    show_featured_image = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Show featured images",
    )
    layout_style = blocks.ChoiceBlock(
        choices=[
            ("list", "List View"),
            ("grid", "Grid View"),
            ("cards", "Card View"),
        ],
        default="cards",
        help_text="Display layout",
    )

    # The images each layout uses, on top of the usual post summary renditions.
    post_image_renditions = {
        "thumb": "fill-128x128",
        "grid": "fill-300x192",
        "cards": "fill-400x192",
    }

    def get_api_representation(self, value, context=None):
        """Adds "posts": the newest live posts, so the frontend needs no second request."""
        from blog.models import BlogPage  # blog.models imports this module

        data = super().get_api_representation(value, context)
        posts = BlogPage.live_posts().order_by("-first_published_at")[: value["number_of_posts"]]
        data["posts"] = [serialize_post_summary(post, self.post_image_renditions) for post in posts]
        return data

    class Meta:
        icon = "list-ul"
        label = "Recent Posts"


class BaseQuoteBlock(APIStructBlock):
    """Blockquote with attribution."""

    quote = blocks.CharBlock(
        required=True,
        help_text="Quote text",
    )
    author = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text="Quote author",
    )
    author_title = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text="Author's title or position",
    )
    style = blocks.ChoiceBlock(
        choices=[
            ("default", "Default"),
            ("large", "Large Quote"),
            ("bordered", "Bordered"),
            ("accent", "Accent Style"),
        ],
        default="default",
        help_text="Quote style",
    )

    class Meta:
        icon = "openquote"
        label = "Quote"


class LinkBlock(blocks.StructBlock):
    """A link in the header navigation or the footer."""

    text = blocks.CharBlock(max_length=50)
    url = blocks.CharBlock(max_length=200, help_text="A path such as /blog/ or a full URL")

    class Meta:
        icon = "link"
        label = "Link"
