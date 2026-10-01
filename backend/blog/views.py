"""The posts API endpoint (see config/urls.py), which serves the blog listing and archives."""

import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from taggit.models import Tag

from core.serializers import serialize_post_summary

from .models import BlogPage

POSTS_PER_PAGE = 12


@csrf_exempt  # Read-only, so safe; other methods get 405, not a CSRF 403.
@require_GET
def posts(request):
    """
    Live posts, newest first, 12 per page, optionally filtered by tag and/or date
    (?tag=slug, ?year=2025, ?year=2025&month=3, ?year=2025&month=3&day=14).
    """
    posts = BlogPage.live_posts()

    tag = None
    if tag_slug := request.GET.get("tag"):
        tag = Tag.objects.filter(slug=tag_slug).first()
        if tag is None:
            return JsonResponse({"detail": "Not found."}, status=404)
        posts = posts.filter(tags__slug=tag.slug)

    try:
        year, month, day = (
            int(request.GET[name]) if request.GET.get(name) else None
            for name in ("year", "month", "day")
        )
    except ValueError:
        return JsonResponse({"detail": "year, month and day must be whole numbers."}, status=400)
    if (month is not None and year is None) or (day is not None and month is None):
        return JsonResponse({"detail": "month needs year, and day needs month."}, status=400)
    if year is not None:
        try:
            # Rejects dates that don't exist, such as month 13, 30 February or year 0.
            datetime.date(year, 1 if month is None else month, 1 if day is None else day)
        except ValueError:
            return JsonResponse({"detail": "Not found."}, status=404)
        posts = posts.filter(date__year=year)
        if month is not None:
            posts = posts.filter(date__month=month)
        if day is not None:
            posts = posts.filter(date__day=day)

    # first_published_at and id only make the order stable for posts on the same date.
    posts = posts.order_by("-date", "-first_published_at", "-id")
    # get_page(): a page number that isn't a number gives page 1, one past the end the last page.
    page = Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get("page"))
    return JsonResponse(
        {
            "count": page.paginator.count,
            "page": page.number,
            "num_pages": page.paginator.num_pages,
            "per_page": POSTS_PER_PAGE,
            "tag": {"name": tag.name, "slug": tag.slug} if tag else None,
            "results": [serialize_post_summary(post) for post in page],
        }
    )
