"""
JSON shapes shared by the pages API, StreamField blocks and the custom API views, so
images, tags and post summaries look the same everywhere the frontend receives them.
"""

from rest_framework import serializers
from wagtail.images.shortcuts import get_renditions_or_not_found

# Renditions every post summary includes: {"name in the JSON": "Wagtail filter spec"}.
POST_SUMMARY_RENDITIONS = {"card": "fill-800x450", "list": "fill-400x300"}


def serialize_image(image, renditions):
    """
    An image as {"id", "title", "renditions": {name: {"url", "width", "height"}}}, or None.
    `renditions` maps each name to a filter spec, e.g. {"card": "fill-800x450"}.
    """
    if image is None:
        return None
    # A missing source file gives a placeholder rendition instead of an error,
    # like Wagtail's {% image %} tag.
    found = get_renditions_or_not_found(image, list(renditions.values()))
    return {
        "id": image.id,
        "title": image.title,
        "renditions": {
            name: {
                "url": found[spec].url,
                "width": found[spec].width,
                "height": found[spec].height,
            }
            for name, spec in renditions.items()
        },
    }


def serialize_datetime(value):
    """ISO 8601 in UTC ending in "Z", formatted exactly like Wagtail's API meta fields."""
    return serializers.DateTimeField().to_representation(value) if value else None


def serialize_tags(post):
    """A post's tags as [{"name", "slug"}], in the order they were added."""
    # Sorted here rather than with order_by(), so prefetched tags and the unsaved
    # tags of a preview work too.
    items = sorted(post.tagged_items.all(), key=lambda item: (item.pk is None, item.pk or 0))
    return [{"name": item.tag.name, "slug": item.tag.slug} for item in items]


def serialize_post_summary(post, extra_renditions=None):
    """A blog post as a PostSummary, used by listings, the home page and recent posts."""
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "url": post.get_date_url(),
        "date": post.date.isoformat(),
        "first_published_at": serialize_datetime(post.first_published_at),
        "intro": post.intro,
        "featured": post.featured,
        "estimated_reading_time": post.estimated_reading_time,
        "tags": serialize_tags(post),
        "featured_image": serialize_image(
            post.featured_image, POST_SUMMARY_RENDITIONS | (extra_renditions or {})
        ),
    }


# Serializer fields for page models' api_fields.


class ImageField(serializers.Field):
    """An image foreign key, with the given named renditions (see serialize_image)."""

    def __init__(self, renditions, **kwargs):
        self.renditions = renditions
        super().__init__(**kwargs)

    def to_representation(self, image):
        return serialize_image(image, self.renditions)


class TagsField(serializers.Field):
    """A post's tags as [{"name", "slug"}]. Use with source="*" (it needs the post)."""

    def to_representation(self, post):
        return serialize_tags(post)


class PostSummariesField(serializers.Field):
    """A list of blog posts as PostSummary objects."""

    def to_representation(self, posts):
        return [serialize_post_summary(post) for post in posts]


class PostLinkField(serializers.Field):
    """A neighbouring blog post as {"title", "url", "intro"}."""

    def to_representation(self, post):
        return {"title": post.title, "url": post.get_date_url(), "intro": post.intro}
