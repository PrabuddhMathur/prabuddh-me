from django import template
from django.utils.safestring import mark_safe
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag
def get_recent_blog_posts(count=5):
    """
    Template tag to fetch recent blog posts.
    Usage: {% get_recent_blog_posts 5 as recent_posts %}
    """
    try:
        from blog.models import BlogPage
        posts = BlogPage.objects.live().public().order_by('-first_published_at')[:count]
        return posts
    except ImportError:
        logger.warning("Blog app not available for recent posts template tag")
        return []
    except Exception as e:
        logger.error(f"Error fetching recent blog posts: {e}")
        return []


@register.simple_tag
def get_featured_blog_posts(count=3):
    """
    Template tag to fetch featured blog posts.
    Usage: {% get_featured_blog_posts 3 as featured_posts %}
    """
    try:
        from blog.models import BlogPage
        posts = BlogPage.objects.live().public().filter(featured=True).order_by('-first_published_at')[:count]
        return posts
    except ImportError:
        logger.warning("Blog app not available for featured posts template tag")
        return []
    except Exception as e:
        logger.error(f"Error fetching featured blog posts: {e}")
        return []


@register.simple_tag
def get_blog_tags():
    """
    Template tag to fetch all blog tags.
    Usage: {% get_blog_tags as all_tags %}
    """
    try:
        from blog.models import BlogPageTag
        tags = BlogPageTag.objects.all().values_list('tag__name', flat=True).distinct()
        return sorted(set(tags))
    except ImportError:
        logger.warning("Blog app not available for tags template tag")
        return []
    except Exception as e:
        logger.error(f"Error fetching blog tags: {e}")
        return []
