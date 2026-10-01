import datetime
import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.text import slugify
from taggit.models import Tag
from wagtail.models import Page

from home.models import HomePage

from .models import BlogPage, count_words


def make_post(title, date, tags=(), body=(), intro="", published_hour=10, **fields):
    """Publishes a post under the home page, with first_published_at fixed to its date."""
    post = BlogPage(
        title=title,
        slug=slugify(title),
        date=date,
        intro=intro,
        body=json.dumps([{"type": type_, "value": value} for type_, value in body]),
        **fields,
    )
    for tag in tags:  # One at a time, so they keep this order.
        post.tags.add(tag)
    HomePage.objects.get().add_child(instance=post)
    post.save_revision().publish()
    stamp = datetime.datetime.combine(date, datetime.time(published_hour), tzinfo=datetime.UTC)
    Page.objects.filter(pk=post.pk).update(first_published_at=stamp, last_published_at=stamp)
    return BlogPage.objects.get(pk=post.pk)


def text_block(html):
    return ("text", {"text": html, "alignment": "left"})


class PostsEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 13 posts, one on the 1st of each month from January 2024 to January 2025.
        cls.posts = [
            make_post(f"Post {n}", datetime.date(2024 + (n - 1) // 12, (n - 1) % 12 + 1, 1))
            for n in range(1, 14)
        ]

    def get(self, query=""):
        return self.client.get(f"/api/v2/posts/{query}")

    def test_first_page_is_newest_twelve(self):
        data = self.get().json()
        self.assertEqual(
            {key: data[key] for key in ("count", "page", "num_pages", "per_page", "tag")},
            {"count": 13, "page": 1, "num_pages": 2, "per_page": 12, "tag": None},
        )
        self.assertEqual(
            [post["title"] for post in data["results"]],
            [f"Post {n}" for n in range(13, 1, -1)],
        )

    def test_post_summary_shape(self):
        summary = self.get().json()["results"][0]
        self.assertEqual(
            summary,
            {
                "id": self.posts[-1].id,
                "title": "Post 13",
                "slug": "post-13",
                "url": "/2025/01/01/post-13/",
                "date": "2025-01-01",
                "first_published_at": "2025-01-01T10:00:00Z",
                "intro": "",
                "featured": False,
                "estimated_reading_time": 1,
                "tags": [],
                "featured_image": None,
            },
        )

    def test_pagination(self):
        self.assertEqual([p["title"] for p in self.get("?page=2").json()["results"]], ["Post 1"])
        # Like Django's Paginator.get_page(): not a number gives page 1, too big the last page.
        self.assertEqual(self.get("?page=abc").json()["page"], 1)
        self.assertEqual(self.get("?page=99").json()["page"], 2)

    def test_unpublished_posts_are_left_out(self):
        self.posts[0].unpublish()
        self.assertEqual(self.get().json()["count"], 12)

    def test_tag_filter(self):
        self.posts[0].tags.add("django")
        self.posts[0].save_revision().publish()
        data = self.get("?tag=django").json()
        self.assertEqual(data["tag"], {"name": "django", "slug": "django"})
        self.assertEqual([p["title"] for p in data["results"]], ["Post 1"])

    def test_known_tag_without_posts(self):
        Tag.objects.create(name="Empty", slug="empty")
        response = self.get("?tag=empty")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)

    def test_unknown_tag_is_404(self):
        response = self.get("?tag=nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_date_filters(self):
        self.assertEqual(self.get("?year=2024").json()["count"], 12)
        self.assertEqual(self.get("?year=2024&month=3").json()["count"], 1)
        self.assertEqual(self.get("?year=2024&month=3&day=1").json()["count"], 1)
        self.assertEqual(self.get("?year=2024&month=3&day=2").json()["count"], 0)
        self.assertEqual(self.get("?year=2023").json()["count"], 0)

    def test_invalid_dates(self):
        for query in ("?year=2024&month=13", "?year=2024&month=2&day=30", "?year=0"):
            with self.subTest(query):
                self.assertEqual(self.get(query).status_code, 404)
        for query in ("?month=3", "?year=2024&day=1", "?year=abc"):
            with self.subTest(query):
                self.assertEqual(self.get(query).status_code, 400)

    def test_get_only(self):
        self.assertEqual(self.client.post("/api/v2/posts/").status_code, 405)


class BlogPageAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.oldest = make_post("Oldest", datetime.date(2025, 1, 1))
        cls.middle = make_post(
            "Middle", datetime.date(2025, 2, 1), tags=["zeta", "alpha"], intro="In between."
        )
        cls.newest = make_post("Newest", datetime.date(2025, 3, 1))

    def get_post(self, slug):
        response = self.client.get(f"/api/v2/pages/?type=blog.BlogPage&slug={slug}&fields=*")
        self.assertEqual(response.status_code, 200)
        return response.json()["items"][0]

    def test_fields(self):
        post = self.get_post("middle")
        self.assertEqual(post["meta"]["type"], "blog.BlogPage")
        self.assertEqual(post["url"], "/2025/02/01/middle/")
        self.assertEqual(post["date"], "2025-02-01")
        self.assertEqual(post["line_height"], "default")
        # In the order they were added, not alphabetical.
        self.assertEqual(
            post["tags"], [{"name": "zeta", "slug": "zeta"}, {"name": "alpha", "slug": "alpha"}]
        )
        for field in ("meta_description", "meta_keywords", "og_title", "og_description"):
            self.assertEqual(post[field], "")
        self.assertIsNone(post["og_image"])
        self.assertIsNone(post["featured_image"])

    def test_previous_and_next(self):
        post = self.get_post("middle")
        self.assertEqual(
            post["previous_post"], {"title": "Oldest", "url": "/2025/01/01/oldest/", "intro": ""}
        )
        self.assertEqual(
            post["next_post"], {"title": "Newest", "url": "/2025/03/01/newest/", "intro": ""}
        )
        self.assertIsNone(self.get_post("oldest")["previous_post"])
        self.assertIsNone(self.get_post("newest")["next_post"])

    def test_page_urls_use_the_date(self):
        self.assertEqual(self.middle.url, "/2025/02/01/middle/")

    def test_find_by_tree_path(self):
        # The frontend redirects posts found at /<slug>/ to their date URL.
        response = self.client.get("/api/v2/pages/find/?html_path=/middle/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["url"], "/2025/02/01/middle/")


class ReadingTimeTests(TestCase):
    def test_counts_words_inside_rich_text(self):
        # The old site skipped rich text blocks, so this post would have been 1 minute.
        post = make_post("Long", datetime.date(2025, 1, 1), body=[text_block("<p>word </p>" * 600)])
        self.assertEqual(post.estimated_reading_time, 3)

    def test_counts_intro_headings_and_quotes(self):
        post = make_post(
            "Mixed",
            datetime.date(2025, 1, 1),
            intro="w " * 100,  # 100 words within the 250-character limit
            body=[
                ("heading", {"heading_text": "word " * 100, "heading_level": "h2"}),
                ("quote", {"quote": "word " * 100, "author": "Someone"}),
                text_block("<ul><li>word</li><li>word</li></ul>"),
            ],
        )
        # 100 + 100 + 1 (author) + 2; choice values such as "h2" and "left" aren't words.
        self.assertEqual(count_words(post.body.stream_block, post.body), 203)
        self.assertEqual(post.get_reading_time(), 2)  # With the intro: 303 words.

    def test_at_least_one_minute(self):
        self.assertEqual(make_post("Empty", datetime.date(2025, 1, 1)).estimated_reading_time, 1)

    def test_future_date_is_invalid(self):
        post = BlogPage(title="Later", slug="later", date=datetime.date(3000, 1, 1))
        post.depth, post.path = 3, "000100010099"  # A place in the tree, which clean() needs.
        with self.assertRaisesMessage(ValidationError, "Post date cannot be in the future."):
            post.clean()
