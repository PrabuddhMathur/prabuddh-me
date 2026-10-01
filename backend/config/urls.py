from django.conf import settings
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from blog import views as blog_views
from core import views as core_views

from .api import api_router

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # Plain JSON views for the frontend. Before the router, which owns the rest of /api/v2/.
    path("api/v2/site/", core_views.site_settings, name="api_site"),
    path("api/v2/posts/", blog_views.posts, name="api_posts"),
    path("api/v2/search/", core_views.search, name="api_search"),
    path("api/v2/", api_router.urls),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from the development server.
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    # Wagtail's page-serving view. Page models use HeadlessMixin, so this redirects to
    # the Nuxt frontend, which is what makes "View live" in the admin work.
    # Must stay last.
    path("", include(wagtail_urls)),
]
