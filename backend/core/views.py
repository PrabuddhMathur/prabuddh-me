"""The site settings and search API endpoints (see config/urls.py)."""

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.defaultfilters import title
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from wagtail.models import Page, Site

from .models import AuthorSettings, FooterSettings, HeaderSettings, SiteSettings, links_as_list
from .serializers import serialize_image

SEARCH_RESULTS_PER_PAGE = 10


@csrf_exempt  # Read-only, so safe; other methods get 405, not a CSRF 403.
@require_GET
def site_settings(request):
    """Header, footer, author and SEO settings of the default site."""
    site = Site.objects.filter(is_default_site=True).first()

    def load(model):
        # Without a site there is nothing to store settings against; use the defaults.
        return model.for_site(site) if site else model()

    settings, header, footer, author = (
        load(model) for model in (SiteSettings, HeaderSettings, FooterSettings, AuthorSettings)
    )
    return JsonResponse(
        {
            "site_name": settings.site_name,
            "default_meta_description": settings.default_meta_description,
            "google_analytics_id": settings.google_analytics_id,
            "header": {
                "site_title": header.site_title,
                "show_logo": header.show_logo,
                "logo": serialize_image(header.logo, {"logo": "fill-32x32"}),
                "navigation": links_as_list(header.navigation),
                "show_search": header.show_search,
                "show_theme_toggle": header.show_theme_toggle,
                "header_style": header.header_style,
            },
            "footer": {
                "copyright_text": footer.copyright_text,
                "show_year": footer.show_year,
                "show_newsletter": footer.show_newsletter,
                "show_quick_links": footer.show_quick_links,
                "links": links_as_list(footer.links),
            },
            "author": {
                "name": author.author_name,
                "title": author.author_title,
                "bio_short": author.author_bio_short,
                "image": serialize_image(author.author_image, {"sidebar": "fill-160x160"}),
                "social_links": author.get_social_links(),
            },
        }
    )


@csrf_exempt  # Read-only, so safe; other methods get 405, not a CSRF 403.
@require_GET
def search(request):
    """Full-text search over all live, public pages, 10 per page."""
    query = request.GET.get("query", "").strip()
    if query:
        # depth 1 is the tree root, which isn't a real page.
        results = Page.objects.live().public().filter(depth__gt=1).specific().search(query)
    else:
        results = Page.objects.none()

    # get_page(): a page number that isn't a number gives page 1, one past the end the last page.
    page = Paginator(results, SEARCH_RESULTS_PER_PAGE).get_page(request.GET.get("page"))
    return JsonResponse(
        {
            "query": query,
            "count": page.paginator.count,
            "page": page.number,
            "num_pages": page.paginator.num_pages,
            "per_page": SEARCH_RESULTS_PER_PAGE,
            "results": [serialize_search_result(result, request) for result in page],
        }
    )


def serialize_search_result(page, request):
    url_parts = page.get_url_parts(request)
    model_name = ContentType.objects.get_for_id(page.content_type_id).model
    return {
        "id": page.id,
        "title": page.title,
        "url": url_parts[2] if url_parts else None,
        "search_description": page.search_description,
        "type": f"{page._meta.app_label}.{type(page).__name__}",
        # The old results page showed content_type.model|title, e.g. "Blogpage".
        "type_label": title(model_name),
    }
