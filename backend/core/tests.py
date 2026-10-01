import datetime
import shutil
import tempfile

from django.test import TestCase, override_settings
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from blog.tests import make_post
from home.models import HomePage

from .blocks import BaseRichTextBlock
from .models import AuthorSettings, StaticPage


class SiteEndpointTests(TestCase):
    def test_defaults(self):
        response = self.client.get("/api/v2/site/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "site_name": "My Site",
                "default_meta_description": "",
                "google_analytics_id": "",
                "header": {
                    "site_title": "My Site",
                    "show_logo": False,
                    "logo": None,
                    "navigation": [
                        {"text": "Home", "url": "/"},
                        {"text": "Blog", "url": "/blog/"},
                        {"text": "About", "url": "/about/"},
                        {"text": "Contact", "url": "/contact/"},
                    ],
                    "show_search": True,
                    "show_theme_toggle": True,
                    "header_style": "sticky",
                },
                "footer": {
                    "copyright_text": "All rights reserved.",
                    "show_year": True,
                    "show_newsletter": True,
                    "show_quick_links": True,
                    "links": [
                        {"text": "About", "url": "/about/"},
                        {"text": "Contact", "url": "/contact/"},
                        {"text": "Privacy", "url": "/privacy/"},
                        {"text": "Terms", "url": "/terms/"},
                    ],
                },
                "author": {
                    "name": "Prabuddh Mathur",
                    "title": "",
                    "bio_short": "",
                    "image": None,
                    "social_links": [],
                },
            },
        )

    def test_author_image_and_social_links(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root)
        with override_settings(MEDIA_ROOT=media_root):
            author = AuthorSettings.for_site(Site.objects.get(is_default_site=True))
            author.author_image = Image.objects.create(
                title="Me", file=get_test_image_file(size=(400, 400))
            )
            author.email_address = "me@example.com"
            author.github_url = "https://github.com/me"
            author.website_url = "https://example.com"
            author.save()

            data = self.client.get("/api/v2/site/").json()["author"]

        image = data["image"]
        self.assertEqual(image["title"], "Me")
        self.assertEqual(set(image["renditions"]), {"sidebar"})
        self.assertEqual(image["renditions"]["sidebar"]["width"], 160)
        self.assertTrue(image["renditions"]["sidebar"]["url"].startswith("/media/images/"))
        # Same order as the old AuthorSettings.get_social_links().
        self.assertEqual(
            data["social_links"],
            [
                {"name": "Website", "url": "https://example.com", "icon": "globe"},
                {"name": "GitHub", "url": "https://github.com/me", "icon": "github"},
                {"name": "Email", "url": "mailto:me@example.com", "icon": "email"},
            ],
        )


class SearchEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        make_post("Wagtail tips", datetime.date(2025, 3, 14), intro="All about zebras.")

    def test_finds_a_post(self):
        data = self.client.get("/api/v2/search/?query=zebras").json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"][0],
            {
                "id": data["results"][0]["id"],
                "title": "Wagtail tips",
                "url": "/2025/03/14/wagtail-tips/",
                "search_description": "",
                "type": "blog.BlogPage",
                # content_type.model|title, like the old results page.
                "type_label": "Blogpage",
            },
        )

    def test_empty_query(self):
        for query in ("", "?query=", "?query=%20"):
            with self.subTest(query):
                self.assertEqual(
                    self.client.get(f"/api/v2/search/{query}").json(),
                    {
                        "query": "",
                        "count": 0,
                        "page": 1,
                        "num_pages": 1,
                        "per_page": 10,
                        "results": [],
                    },
                )

    def test_page_that_is_not_a_number(self):
        data = self.client.get("/api/v2/search/?query=zebras&page=abc").json()
        self.assertEqual((data["page"], data["count"]), (1, 1))


class FindEndpointTests(TestCase):
    def test_home_page(self):
        response = self.client.get("/api/v2/pages/find/?html_path=/")
        # Returned directly, not as a redirect to the detail URL.
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["meta"]["type"], "home.HomePage")
        self.assertEqual(data["featured_posts"], [])

    def test_static_page(self):
        about = StaticPage(title="About", slug="about", intro="Hello.", show_last_updated=True)
        HomePage.objects.get().add_child(instance=about)
        about.save_revision().publish()

        response = self.client.get("/api/v2/pages/find/?html_path=/about/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["meta"]["type"], "core.StaticPage")
        self.assertEqual(data["intro"], "Hello.")
        self.assertEqual(data["body"], [])
        self.assertIsNotNone(data["last_updated"])

    def test_missing_page(self):
        self.assertEqual(self.client.get("/api/v2/pages/find/?html_path=/nope/").status_code, 404)


class SpoilerFeatureTests(TestCase):
    def test_round_trip(self):
        features = BaseRichTextBlock().child_blocks["text"].features
        converter = ContentstateConverter(features=features)
        html = '<p>a <span class="spoiler" data-spoiler="true">b</span></p>'

        contentstate = converter.from_database_format(html)
        self.assertIn('"style": "SPOILER"', contentstate)
        self.assertIn(
            '<span class="spoiler" data-spoiler="true">b</span>',
            converter.to_database_format(contentstate),
        )
