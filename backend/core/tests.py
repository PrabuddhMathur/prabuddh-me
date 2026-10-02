import datetime
import json
import shutil
import tempfile
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.template.loader import get_template
from django.test import RequestFactory, TestCase, override_settings
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from blog.tests import make_post
from home.models import HomePage

from . import emails, form_posts
from .blocks import BaseRichTextBlock
from .models import AuthorSettings, SiteSettings, StaticPage


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


class FormPostsTests(TestCase):
    """The helpers behind the newsletter and comment endpoints."""

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def json_request(self, body, **extra):
        return self.factory.post(
            "/",
            body if isinstance(body, str) else json.dumps(body),
            content_type="application/json",
            **extra,
        )

    def test_is_json(self):
        self.assertTrue(form_posts.is_json(self.json_request({})))
        self.assertFalse(form_posts.is_json(self.factory.post("/", {"a": "b"})))

    def test_read_body_reads_json_or_a_form(self):
        self.assertEqual(form_posts.read_body(self.json_request({"a": 1})), {"a": 1})
        self.assertEqual(form_posts.read_body(self.factory.post("/", {"a": "b"})), {"a": "b"})
        # Anything that isn't a JSON object reads as no fields at all.
        for body in ("{nope", "[1, 2]", '"text"', "", "null"):
            self.assertEqual(form_posts.read_body(self.json_request(body)), {}, body)

    def test_text_only_lets_strings_through(self):
        self.assertEqual(form_posts.text("a"), "a")
        for value in (None, 5, ["a"], {"a": 1}, True):
            self.assertEqual(form_posts.text(value), "")

    def test_client_ip_prefers_the_proxys_header(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_REAL_IP="203.0.113.5")
        self.assertEqual(form_posts.client_ip(request), "203.0.113.5")
        self.assertEqual(
            form_posts.client_ip(self.factory.get("/", REMOTE_ADDR="10.0.0.1")), "10.0.0.1"
        )
        request = self.factory.get("/")
        del request.META["REMOTE_ADDR"]
        self.assertEqual(form_posts.client_ip(request), "")

    def test_throttled_counts_per_scope_and_address(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.1")
        other = self.factory.get("/", REMOTE_ADDR="10.0.0.2")
        self.assertEqual(
            [form_posts.throttled(request, "a", 2) for _ in range(4)], [False, False, True, True]
        )
        self.assertFalse(form_posts.throttled(request, "b", 2))  # Another scope.
        self.assertFalse(form_posts.throttled(other, "a", 2))  # Another visitor.
        self.assertEqual(cache.get("a:10.0.0.1"), 4)

    def test_throttled_window_is_the_cache_lifetime_of_the_count(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.1")
        with mock.patch.object(form_posts.cache, "add") as add:
            form_posts.throttled(request, "a", 2, window=60)
        add.assert_called_once_with("a:10.0.0.1", 0, 60)
        self.assertEqual(form_posts.THROTTLE_WINDOW, 3600)

    def test_throttled_survives_the_count_expiring_between_two_calls(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.1")
        with mock.patch.object(form_posts.cache, "incr", side_effect=ValueError):
            self.assertFalse(form_posts.throttled(request, "a", 2))
        self.assertEqual(cache.get("a:10.0.0.1"), 1)

    def test_see_other_is_a_303(self):
        response = form_posts.see_other("/next/?a=b")
        self.assertEqual((response.status_code, response["Location"]), (303, "/next/?a=b"))

    def test_clean_email(self):
        self.assertEqual(form_posts.clean_email("  Ann@Example.COM "), "ann@example.com")
        long_ok = "x" * 64 + "@" + "a" * 63 + "." + "b" * 63 + "." + "c" * 57 + ".com"
        self.assertEqual(len(long_ok), 254)
        self.assertEqual(form_posts.clean_email(long_ok), long_ok)
        for bad in ("", "  ", "nope", "a@b", "a b@example.com", long_ok + "x", None, 5, ["a@b.co"]):
            self.assertIsNone(form_posts.clean_email(bad), bad)


@override_settings(
    FRONTEND_URL="https://example.org/", DEFAULT_FROM_EMAIL="Blog <news@example.org>"
)
class EmailHelperTests(TestCase):
    def test_frontend_url_is_absolute_whatever_the_trailing_slash(self):
        self.assertEqual(emails.frontend_url(), "https://example.org")
        self.assertEqual(emails.frontend_url("/a/?b=c"), "https://example.org/a/?b=c")

    def test_site_name_comes_from_the_settings_then_the_default(self):
        site_settings = SiteSettings.for_site(Site.objects.get(is_default_site=True))
        site_settings.site_name = "Renamed"
        site_settings.save()
        self.assertEqual(emails.site_name(), "Renamed")
        site_settings.site_name = ""
        site_settings.save()
        self.assertEqual(emails.site_name(), "Prabuddh's Blog")

    def test_one_line(self):
        self.assertEqual(emails.one_line("a\n b\r\n\tc"), "a b c")

    def test_build_email_renders_both_templates_with_the_shared_layout(self):
        message = emails.build_email(
            "Confirm\nthis",
            "newsletter/emails/confirm",
            {"confirm_url": "https://example.org/c/"},
            to=["a@example.com"],
            headers={"X-Test": "1"},
        )
        self.assertEqual(message.subject, "Confirm this")
        self.assertEqual(
            (message.to, message.from_email), (["a@example.com"], "Blog <news@example.org>")
        )
        self.assertEqual(message.extra_headers["X-Test"], "1")
        self.assertRegex(message.message()["Message-ID"], r"^<[^@>]+@example\.org>$")
        self.assertIn("https://example.org/c/", message.body)
        html = emails.html_of(message)
        self.assertIn("<title>Confirm\nthis</title>", html)  # The raw subject, from the layout.
        self.assertIn(emails.BUTTON_COLOR, html)
        self.assertIn(emails.BUTTON_TEXT_COLOR, html)
        self.assertIn('href="https://example.org/"', html)  # The site link in the layout.

    def test_build_email_uses_the_connection_and_headers_can_replace_the_message_id(self):
        connection = mail.get_connection()
        message = emails.build_email(
            "Hi",
            "newsletter/emails/confirm",
            {"confirm_url": "x"},
            to=["a@example.com"],
            headers={"Message-ID": "<fixed@example.org>"},
            connection=connection,
        )
        self.assertIs(message.connection, connection)
        self.assertEqual(message.extra_headers["Message-ID"], "<fixed@example.org>")

    def test_the_layout_lives_in_core(self):
        self.assertIn("core/emails/base.html", get_template("core/emails/base.html").template.name)
