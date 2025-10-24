from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from blog import views as blog_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    
    # Blog URLs (order matters: most specific first)
    path("blog/", blog_views.blog_listing, name="blog_listing"),
    path("blog/author/<slug:author_slug>/", blog_views.blog_author_archive, name="blog_author_archive"),
    path("blog/tag/<slug:tag_slug>/", blog_views.blog_tag_archive, name="blog_tag_archive"),
    
    # Blog date-based URLs
    path("<int:year>/<int:month>/<int:day>/<slug:slug>/", blog_views.blog_post_detail, name="blog_post_detail"),
    path("<int:year>/<int:month>/<int:day>/", blog_views.blog_day_archive, name="blog_day_archive"),
    path("<int:year>/<int:month>/", blog_views.blog_month_archive, name="blog_month_archive"),
    path("<int:year>/", blog_views.blog_year_archive, name="blog_year_archive"),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from core.test_error_views import test_404, test_500

    # Test URLs for error pages
    urlpatterns += [
        path("test-404/", test_404, name="test_404"),
        path("test-500/", test_500, name="test_500"),
    ]

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
