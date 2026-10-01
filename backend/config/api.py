from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from wagtail.api.v2 import views
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail_headless_preview.models import PagePreview

from blog.models import BlogPage


class PagesAPIViewSet(views.PagesAPIViewSet):
    """
    Wagtail's pages endpoint, except that /find/ returns the page itself instead of
    redirecting to its detail URL. That redirect is an absolute URL built from
    WAGTAILAPI_BASE_URL, which the Nuxt server can't reach from inside Docker.
    """

    def find_view(self, request):
        try:
            page = self.find_object(self.get_queryset(), request)
        except self.model.DoesNotExist:
            page = None
        if page is None:
            raise Http404("not found")
        # detail_view() serialises whatever get_object() returns, and get_object() caches.
        self._cached_object = page
        return self.detail_view(request, page.pk)


class PagePreviewAPIViewSet(views.PagesAPIViewSet):
    """
    Returns a draft page for the frontend's /preview page, looked up by the
    content type and token that wagtail-headless-preview puts in the preview URL.
    """

    known_query_parameters = views.PagesAPIViewSet.known_query_parameters.union(
        ["content_type", "token"]
    )

    def listing_view(self, request):
        # Serialise exactly like a detail view.
        self.action = "detail_view"
        return self.detail_view(request, 0)

    def get_object(self):
        # Cached, because choosing the serializer and serialising both call this.
        if not hasattr(self, "_cached_object"):
            self._cached_object = self.get_preview_page()
        return self._cached_object

    def get_preview_page(self):
        try:
            app_label, model = self.request.GET["content_type"].split(".")
            token = self.request.GET["token"]
        except (KeyError, ValueError) as exc:
            raise Http404 from exc

        content_type = get_object_or_404(ContentType, app_label=app_label, model=model)
        page_preview = get_object_or_404(PagePreview, content_type=content_type, token=token)
        page = page_preview.as_page()
        if not page.pk:
            # A never-published page has no primary key; the API's URL routing needs one.
            page.pk = 0
        if isinstance(page, BlogPage):
            # The reading time is only calculated when a post is saved, and drafts aren't.
            page.estimated_reading_time = page.get_reading_time()
        return page


api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", PagesAPIViewSet)
api_router.register_endpoint("page_preview", PagePreviewAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
