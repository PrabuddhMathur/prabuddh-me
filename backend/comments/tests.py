import datetime
import json
import logging
import time
from io import StringIO
from unittest import mock
from urllib.parse import parse_qsl

import httpx
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.cache import cache
from django.core.checks import registry as checks_registry
from django.core.mail.backends import locmem
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from wagtail.admin.views.bulk_action.registry import bulk_action_registry
from wagtail.models import Page, Site

from blog.models import BlogPage
from blog.tests import make_post
from core.emails import html_of
from core.models import AuthorSettings
from home.models import HomePage
from newsletter.management.commands import newsletter_worker

from . import emails, housekeeping, moderation, spam, views
from .checks import check_akismet_configured
from .models import Comment, CommentSettings
from .text import MAX_BODY_LENGTH, clean_body, clean_name
from .wagtail_hooks import (
    CommentPermissionPolicy,
    CommentsMenuItem,
    DeleteCommentsBulkAction,
    PendingCommentsSummaryItem,
)

# Expected failures are logged by the code under test; keep them out of the test output.
logging.getLogger("comments").addHandler(logging.NullHandler())
logging.getLogger("newsletter").addHandler(logging.NullHandler())

COMMENTS = "/api/v2/comments/"
CONFIRM = "/api/v2/comments/alerts/confirm/"
STOP = "/api/v2/comments/alerts/stop/"
POST_URL = "/2024/05/03/hello-world/"


class FailingBackend(locmem.EmailBackend):
    """A mail server that is down."""

    def send_messages(self, email_messages):
        raise ConnectionRefusedError("the mail server is down")


class CountingBackend(locmem.EmailBackend):
    """The test email backend, counting how often a connection is opened."""

    opened = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_open = False

    def open(self):
        if self.is_open:
            return False
        self.is_open = True
        CountingBackend.opened += 1
        return True

    def close(self):
        self.is_open = False


class UnreachableBackend(locmem.EmailBackend):
    """A mail server nobody can connect to, counting the tries."""

    attempts = 0

    def open(self):
        UnreachableBackend.attempts += 1
        raise TimeoutError("timed out")


class FakeAkismet:
    """
    Stands in for the Akismet web service: answers every request itself and records them.
    The real library and real HTTP client run, so the requests are what would be sent.
    """

    THANKS = "Thanks for making the web a better place."

    def __init__(self, verdict="ham", *, error=None, status=200, body=None):
        self.verdict = verdict  # "ham", "spam" or "discard"
        self.error = error  # Raised by the "network".
        self.status = status
        self.body = body  # Overrides the answer, e.g. "invalid".
        self.requests = []  # (endpoint, parameters)
        self.clients = []  # The arguments httpx.Client was created with.

    def handle(self, request):
        endpoint = request.url.path.rsplit("/", 1)[-1]
        self.requests.append((endpoint, dict(parse_qsl(request.content.decode()))))
        if self.error:
            raise self.error
        if self.body is not None:
            return httpx.Response(self.status, text=self.body)
        if endpoint == "comment-check":
            headers = {"X-akismet-pro-tip": "discard"} if self.verdict == "discard" else {}
            text = "false" if self.verdict == "ham" else "true"
            return httpx.Response(self.status, text=text, headers=headers)
        return httpx.Response(self.status, text=self.THANKS)

    def __enter__(self):
        real_client = httpx.Client

        def make_client(**kwargs):
            self.clients.append(kwargs)
            return real_client(transport=httpx.MockTransport(self.handle), **kwargs)

        self.patcher = mock.patch.object(httpx, "Client", make_client)
        self.patcher.start()
        return self

    def __exit__(self, *exc_info):
        self.patcher.stop()

    @property
    def checks(self):
        return [params for endpoint, params in self.requests if endpoint == "comment-check"]

    @property
    def reports(self):
        return [
            (endpoint, params)
            for endpoint, params in self.requests
            if endpoint in ("submit-spam", "submit-ham")
        ]


def old_token():
    """A form token as an hour-old form would have."""
    return views.make_form_token(time.time() - 3600)


def make_comment(post, name="Ann", email="ann@example.com", body="Hello there", **fields):
    return Comment.objects.create(post=post, name=name, email=email, body=body, **fields)


def approved(post, **fields):
    return make_comment(post, status=Comment.APPROVED, **fields)


def set_created(comment, when):
    Comment.objects.filter(pk=comment.pk).update(created_at=when)


def set_comment_settings(**fields):
    site = Site.objects.get(is_default_site=True)
    CommentSettings.objects.update_or_create(site=site, defaults=fields)


class CommentsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.post = make_post("Hello World", datetime.date(2024, 5, 3), published_hour=9)

    def setUp(self):
        cache.clear()  # The post throttle lives in the cache.

    def post_json(self, url, data, **extra):
        return self.client.post(url, json.dumps(data), content_type="application/json", **extra)


# Models


class ModelTests(CommentsTestCase):
    def test_a_new_comment_waits_for_review_and_has_nothing_switched_on(self):
        comment = make_comment(self.post)
        self.assertEqual(comment.status, Comment.PENDING)
        self.assertEqual(comment.spam_check, Comment.UNCHECKED)
        self.assertEqual(comment.reply_alerts, Comment.ALERTS_OFF)
        self.assertFalse(comment.is_author)
        self.assertFalse(comment.liked)
        self.assertIsNone(comment.reviewed_at)
        self.assertIsNotNone(comment.created_at)

    def test_tokens_are_unique_and_long(self):
        a, b = make_comment(self.post), make_comment(self.post)
        self.assertNotEqual(a.token, b.token)
        self.assertGreaterEqual(len(a.token), 40)

    def test_email_is_stripped_and_lower_cased_when_saved(self):
        comment = make_comment(self.post, email="  Ann@Example.COM ")
        self.assertEqual(comment.email, "ann@example.com")
        comment.email = "BOB@example.com"
        comment.save()
        comment.refresh_from_db()
        self.assertEqual(comment.email, "bob@example.com")

    def test_root_is_the_top_level_comment_of_the_thread(self):
        top = make_comment(self.post)
        reply = make_comment(self.post, parent=top)
        deeper = make_comment(self.post, parent=reply)
        deepest = make_comment(self.post, parent=deeper)
        self.assertIsNone(top.root_id)
        self.assertEqual([c.root_id for c in (reply, deeper, deepest)], [top.pk] * 3)
        self.assertEqual(set(top.thread_replies.all()), {reply, deeper, deepest})
        self.assertEqual(list(reply.replies.all()), [deeper])

    def test_saving_a_few_fields_keeps_the_root(self):
        top = make_comment(self.post)
        reply = make_comment(self.post, parent=top)
        reply.status = Comment.APPROVED
        reply.save(update_fields=["status"])
        reply.refresh_from_db()
        self.assertEqual((reply.status, reply.root_id), (Comment.APPROVED, top.pk))

    def test_deleting_a_comment_deletes_its_replies_and_a_post_its_comments(self):
        top = make_comment(self.post)
        reply = make_comment(self.post, parent=top)
        make_comment(self.post, parent=reply)
        other = make_comment(self.post)
        top.delete()
        self.assertEqual(list(Comment.objects.all()), [other])
        BlogPage.objects.get(pk=self.post.pk).delete()
        self.assertEqual(Comment.objects.count(), 0)

    def test_excerpt_is_one_line_and_short(self):
        self.assertEqual(
            make_comment(self.post, body="One\n\ntwo   three").excerpt(), "One two three"
        )
        long = make_comment(self.post, body="word " * 40)
        self.assertEqual(len(long.excerpt()), 80)
        self.assertTrue(long.excerpt().endswith("…"))
        self.assertEqual(len(long.excerpt(20)), 20)

    @override_settings(FRONTEND_URL="https://example.org/")
    def test_public_url_points_at_the_comment_on_the_post_page(self):
        comment = make_comment(self.post)
        self.assertEqual(
            comment.public_url(), f"https://example.org{POST_URL}#comment-{comment.pk}"
        )

    def test_str_names_the_commenter_and_the_post(self):
        self.assertEqual(str(make_comment(self.post, name="Ann")), "Ann on Hello World")

    def test_comments_are_oldest_first(self):
        first, second = make_comment(self.post), make_comment(self.post)
        set_created(first, timezone.now())
        self.assertEqual(list(Comment.objects.all()), [second, first])

    def test_settings_defaults(self):
        site = Site.objects.get(is_default_site=True)
        comment_settings = CommentSettings.for_site(site)
        self.assertTrue(comment_settings.enabled)
        self.assertEqual(comment_settings.like_label, "Liked by Prabuddh")
        self.assertEqual(CommentSettings._meta.verbose_name, "Comments")

    def test_posts_allow_comments_by_default(self):
        self.assertTrue(self.post.allow_comments)
        self.assertIn(
            "allow_comments",
            [
                panel.field_name
                for group in BlogPage.settings_panels
                for panel in getattr(group, "children", [group])
                if hasattr(panel, "field_name")
            ],
        )

    def test_settings_have_the_documented_defaults(self):
        from django.conf import settings

        self.assertEqual(settings.AKISMET_API_KEY, "")
        self.assertFalse(settings.AKISMET_TEST_MODE)
        self.assertEqual(settings.COMMENTS_POST_LIMIT, 10)
        self.assertFalse(settings.WAGTAILADMIN_COMMENTS_ENABLED)


class TextTests(TestCase):
    def test_names(self):
        self.assertEqual(clean_name("  Ann \n  Lee\t"), ("Ann Lee", None))
        self.assertEqual(clean_name(" \n ")[1], "Please enter your name.")
        self.assertEqual(clean_name("x" * 80), ("x" * 80, None))
        self.assertIn("80", clean_name("x" * 81)[1])

    def test_bodies(self):
        self.assertEqual(clean_body("  Hi  \r\n there \r\n"), ("Hi\n there", None))
        self.assertEqual(clean_body("a\n\n\n\n\nb"), ("a\n\nb", None))
        self.assertEqual(clean_body("a\rb"), ("a\nb", None))
        self.assertEqual(clean_body("a  \n  b  "), ("a\n  b", None))  # Leading spaces stay.
        self.assertEqual(clean_body(" \n\n ")[1], "Please write a comment.")
        self.assertEqual(clean_body("x" * MAX_BODY_LENGTH)[1], None)
        self.assertEqual(
            clean_body("x" * (MAX_BODY_LENGTH + 1))[1], "Comments can be at most 5,000 characters."
        )


# Public API: listing


class ListTests(CommentsTestCase):
    def get(self, post=None, **extra):
        post_id = (post or self.post).pk
        return self.client.get(COMMENTS, {"post": post_id}, **extra)

    def test_shape(self):
        approved(self.post, name="Ann", body="Hi", liked=True)
        data = self.get().json()
        self.assertEqual(
            sorted(data),
            ["akismet", "comments", "count", "enabled", "form_token", "like_label", "open"],
        )
        self.assertEqual(
            {key: data[key] for key in ("enabled", "open", "like_label", "akismet", "count")},
            {
                "enabled": True,
                "open": True,
                "like_label": "Liked by Prabuddh",
                "akismet": False,
                "count": 1,
            },
        )
        [thread] = data["comments"]
        comment = Comment.objects.get()
        self.assertEqual(
            thread,
            {
                "id": comment.pk,
                "name": "Ann",
                "body": "Hi",
                "created_at": comment.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "is_author": False,
                "liked": True,
                "replies": [],
            },
        )

    def test_private_details_are_never_listed(self):
        approved(self.post, ip_address="203.0.113.5", user_agent="Agent", referrer="https://x.y")
        body = self.get().content.decode()
        for secret in ("ann@example.com", "203.0.113.5", "Agent", "https://x.y"):
            self.assertNotIn(secret, body)
        self.assertNotIn(Comment.objects.get().token, body)

    def test_only_approved_comments_show(self):
        approved(self.post, name="Shown")
        make_comment(self.post, name="Waiting")
        make_comment(self.post, name="Junk", status=Comment.SPAM)
        approved(make_post("Other", datetime.date(2024, 5, 4)), name="Elsewhere")
        data = self.get().json()
        self.assertEqual([c["name"] for c in data["comments"]], ["Shown"])
        self.assertEqual(data["count"], 1)

    def test_a_thread_is_flattened_oldest_first_and_top_level_comments_are_oldest_first(self):
        now = timezone.now()
        late = approved(self.post, name="Late top")
        early = approved(self.post, name="Early top")
        r1 = approved(self.post, name="Reply 1", parent=early)
        r3 = approved(self.post, name="Reply 3", parent=r1)
        r2 = approved(self.post, name="Reply 2", parent=early)
        for offset, comment in enumerate([early, r1, r2, r3, late]):
            set_created(comment, now + datetime.timedelta(minutes=offset))
        data = self.get().json()
        self.assertEqual([c["name"] for c in data["comments"]], ["Early top", "Late top"])
        self.assertEqual(
            [r["name"] for r in data["comments"][0]["replies"]], ["Reply 1", "Reply 2", "Reply 3"]
        )
        self.assertEqual(data["comments"][1]["replies"], [])
        self.assertEqual(data["count"], 5)

    def test_reply_to_names_the_comment_answered_unless_it_is_the_top_one(self):
        top = approved(self.post, name="Ann")
        author = approved(self.post, name="Prabuddh Mathur", parent=top, is_author=True)
        approved(self.post, name="Bob", parent=author)
        [thread] = self.get().json()["comments"]
        first, second = thread["replies"]
        self.assertIsNone(first["reply_to"])
        self.assertTrue(first["is_author"])
        self.assertEqual(second["reply_to"], {"id": author.pk, "name": "Prabuddh Mathur"})
        self.assertNotIn("reply_to", thread)

    def test_replies_whose_parent_or_root_is_not_approved_are_hidden(self):
        top = approved(self.post, name="Top")
        waiting = make_comment(self.post, name="Waiting", parent=top)
        approved(self.post, name="Under waiting", parent=waiting)
        approved(self.post, name="Fine", parent=top)
        spam_top = make_comment(self.post, name="Spam top", status=Comment.SPAM)
        approved(self.post, name="Under spam", parent=spam_top)
        data = self.get().json()
        self.assertEqual([c["name"] for c in data["comments"]], ["Top"])
        self.assertEqual([r["name"] for r in data["comments"][0]["replies"]], ["Fine"])
        self.assertEqual(data["count"], 2)

    def test_disabled_comments_show_nothing_and_are_closed(self):
        approved(self.post)
        set_comment_settings(enabled=False, like_label="Hearted")
        data = self.get().json()
        self.assertEqual(
            (data["enabled"], data["open"], data["count"], data["comments"]), (False, False, 0, [])
        )
        self.assertEqual(data["like_label"], "Hearted")
        self.assertTrue(data["form_token"])

    def test_a_closed_post_still_shows_its_comments(self):
        approved(self.post)
        BlogPage.objects.filter(pk=self.post.pk).update(allow_comments=False)
        data = self.get().json()
        self.assertEqual((data["enabled"], data["open"], data["count"]), (True, False, 1))

    @override_settings(AKISMET_API_KEY="a-key")
    def test_it_says_when_akismet_is_on(self):
        self.assertTrue(self.get().json()["akismet"])

    def test_a_post_that_is_not_live_or_not_there_is_a_404(self):
        draft = make_post("A Draft", datetime.date(2024, 6, 1))
        Page.objects.filter(pk=draft.pk).update(live=False)
        home = HomePage.objects.get()
        for value in (draft.pk, 999999, home.pk, "abc", "", "1.5", "9" * 40, "-1"):
            response = self.client.get(COMMENTS, {"post": value})
            self.assertEqual(
                (response.status_code, response.json()), (404, {"status": "not_found"}), value
            )
        self.assertEqual(self.client.get(COMMENTS).status_code, 404)

    def test_the_number_of_queries_does_not_grow_with_the_comments(self):
        top = approved(self.post)
        self.get()  # The first request fills the caches (the site and its settings).
        with CaptureQueriesContext(connection) as few:
            self.get()
        for n in range(10):
            reply = approved(self.post, name=f"Reply {n}", parent=top)
            approved(self.post, name=f"Deeper {n}", parent=reply)
            approved(self.post, name=f"Top {n}")
        with CaptureQueriesContext(connection) as many:
            self.get()
        self.assertEqual(len(few), len(many))
        self.assertLessEqual(len(many), 6)

    def test_the_form_token_is_one_of_ours(self):
        token = self.get().json()["form_token"]
        self.assertLess(views.form_token_age(token), 5)

    def test_other_methods_are_405(self):
        self.assertEqual(self.client.put(COMMENTS).status_code, 405)
        self.assertEqual(self.client.delete(COMMENTS).status_code, 405)


# Public API: posting


@override_settings(COMMENTS_POST_LIMIT=1000)
class PostTests(CommentsTestCase):
    def payload(self, **fields):
        return {
            "post": self.post.pk,
            "name": "Ann",
            "email": "Ann@Example.com",
            "body": "Nice post",
            "website": "",
            "form_token": old_token(),
            **fields,
        }

    def submit(self, extra=None, **fields):
        return self.post_json(COMMENTS, self.payload(**fields), **(extra or {}))

    def assertPending(self, response):
        self.assertEqual((response.status_code, response.json()), (200, {"status": "pending"}))

    def test_a_comment_waits_for_review_and_nobody_is_emailed(self):
        self.assertPending(self.submit())
        comment = Comment.objects.get()
        self.assertEqual(
            (comment.status, comment.spam_check, comment.reply_alerts),
            (Comment.PENDING, Comment.UNCHECKED, Comment.ALERTS_OFF),
        )
        self.assertEqual(
            (comment.post, comment.parent, comment.name, comment.email, comment.body),
            (self.post, None, "Ann", "ann@example.com", "Nice post"),
        )
        self.assertFalse(comment.is_author)
        self.assertEqual(mail.outbox, [])

    def test_a_post_id_can_be_a_string(self):
        self.assertPending(self.submit(post=str(self.post.pk)))
        self.assertEqual(Comment.objects.count(), 1)

    def test_the_visitors_details_are_not_kept_without_akismet(self):
        self.submit(extra={"HTTP_USER_AGENT": "Agent", "HTTP_REFERER": "https://x.y/"})
        comment = Comment.objects.get()
        self.assertEqual((comment.ip_address, comment.user_agent, comment.referrer), (None, "", ""))

    def test_asking_for_reply_alerts_is_recorded_but_not_switched_on(self):
        self.submit(notify_replies=True)
        self.assertEqual(Comment.objects.get().reply_alerts, Comment.ALERTS_REQUESTED)
        self.assertEqual(mail.outbox, [])

    def test_only_a_true_checkbox_asks_for_alerts(self):
        for value in (False, None, "", "no", 0, "off"):
            Comment.objects.all().delete()
            self.submit(notify_replies=value)
            self.assertEqual(Comment.objects.get().reply_alerts, Comment.ALERTS_OFF, value)

    def test_a_plain_form_post_works_and_redirects_back_to_the_post(self):
        data = {**self.payload(notify_replies="on"), "name": "Form Ann"}
        response = self.client.post(COMMENTS, data)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], f"{POST_URL}?comment=pending#comment-form")
        comment = Comment.objects.get()
        self.assertEqual((comment.name, comment.reply_alerts), ("Form Ann", "requested"))

    def test_a_form_post_without_the_checkbox_does_not_ask_for_alerts(self):
        self.client.post(COMMENTS, self.payload())
        self.assertEqual(Comment.objects.get().reply_alerts, Comment.ALERTS_OFF)

    def test_form_posts_are_told_what_went_wrong(self):
        invalid = self.client.post(COMMENTS, self.payload(name=""))
        self.assertEqual(invalid["Location"], f"{POST_URL}?comment=invalid#comment-form")
        BlogPage.objects.filter(pk=self.post.pk).update(allow_comments=False)
        closed = self.client.post(COMMENTS, self.payload())
        self.assertEqual(closed["Location"], f"{POST_URL}?comment=closed#comment-form")
        self.assertEqual(Comment.objects.count(), 0)

    def test_a_reply_posted_as_a_form_that_failed_goes_back_to_the_same_reply_form(self):
        parent = approved(self.post)
        invalid = self.client.post(COMMENTS, self.payload(parent=parent.pk, body=""))
        self.assertEqual(
            invalid["Location"], f"{POST_URL}?comment=invalid&replyto={parent.pk}#comment-form"
        )
        done = self.client.post(COMMENTS, self.payload(parent=parent.pk))
        self.assertEqual(done["Location"], f"{POST_URL}?comment=pending#comment-form")

    def test_a_form_post_to_a_missing_post_goes_to_the_home_page(self):
        response = self.client.post(COMMENTS, self.payload(post=999999))
        self.assertEqual((response.status_code, response["Location"]), (303, "/"))

    def test_the_name_is_cleaned_and_must_be_1_to_80_characters(self):
        self.submit(name="  Ann \n  Lee  ")
        self.assertEqual(Comment.objects.get().name, "Ann Lee")
        for bad in ("", "   ", None, 5, ["Ann"], "x" * 81):
            response = self.submit(name=bad)
            self.assertEqual(response.status_code, 400, bad)
            self.assertEqual(sorted(response.json()["errors"]), ["name"], bad)
        self.assertEqual(self.submit(name="x" * 80).status_code, 200)
        self.assertEqual(self.submit(name="").json()["errors"]["name"], "Please enter your name.")

    def test_the_email_must_be_valid(self):
        for bad in ("", "nope", "a@b", "x" * 250 + "@example.com", None, 5, "a b@example.com"):
            response = self.submit(email=bad)
            self.assertEqual(response.status_code, 400, bad)
            self.assertEqual(
                response.json(),
                {"status": "invalid", "errors": {"email": "Please enter a valid email address."}},
            )
        self.assertEqual(Comment.objects.count(), 0)

    def test_the_text_is_cleaned_and_must_be_1_to_5000_characters(self):
        self.submit(body="  Line one  \r\n\r\n\r\n\r\nLine   two \r\n")
        self.assertEqual(Comment.objects.get().body, "Line one\n\nLine   two")
        for bad in ("", " \n ", None, ["x"]):
            response = self.submit(body=bad)
            self.assertEqual(response.json()["errors"], {"body": "Please write a comment."}, bad)
        too_long = self.submit(body="x" * 5001)
        self.assertEqual(
            too_long.json()["errors"], {"body": "Comments can be at most 5,000 characters."}
        )
        self.assertEqual(self.submit(body="x" * 5000).status_code, 200)

    def test_every_problem_is_reported_at_once(self):
        response = self.submit(name="", email="x", body="", parent=999999)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(sorted(response.json()["errors"]), ["body", "email", "name", "parent"])
        self.assertEqual(
            response.json()["errors"]["parent"], "The comment you're replying to isn't available."
        )

    def test_a_reply_needs_an_approved_comment_on_the_same_post(self):
        top = approved(self.post)
        self.assertPending(self.submit(parent=top.pk))
        reply = Comment.objects.get(body="Nice post")
        self.assertEqual((reply.parent, reply.root_id), (top, top.pk))
        self.assertPending(self.submit(parent=str(top.pk), body="By form id"))
        self.assertPending(self.submit(parent=None, body="No parent"))
        self.assertPending(self.submit(parent="", body="Empty parent"))
        self.assertIsNone(Comment.objects.get(body="Empty parent").parent)

        waiting = make_comment(self.post)
        junk = make_comment(self.post, status=Comment.SPAM)
        elsewhere = approved(make_post("Other", datetime.date(2024, 5, 4)))
        before = Comment.objects.count()
        for bad in (waiting.pk, junk.pk, elsewhere.pk, 999999, "abc", [1], {"id": 1}, "9" * 40):
            response = self.submit(parent=bad)
            self.assertEqual(response.status_code, 400, bad)
            self.assertEqual(sorted(response.json()["errors"]), ["parent"], bad)
        self.assertEqual(Comment.objects.count(), before)

    def test_a_reply_to_a_reply_belongs_to_the_same_thread(self):
        top = approved(self.post)
        reply = approved(self.post, parent=top)
        self.submit(parent=reply.pk)
        self.assertEqual(Comment.objects.get(body="Nice post").root_id, top.pk)

    def test_the_honeypot_gets_a_pending_answer_and_nothing_is_stored(self):
        self.assertPending(self.submit(website="http://spam.example"))
        self.assertEqual(Comment.objects.count(), 0)

    def test_a_missing_forged_or_fresh_form_token_gets_a_pending_answer_and_nothing_is_stored(self):
        other_salt = views.signing.TimestampSigner(salt="something.else")
        tokens = {
            "missing": None,
            "empty": "",
            "garbage": "not-a-token",
            "forged": old_token()[:-3] + "xyz",
            "wrong salt": other_salt.sign(str(int(time.time() - 3600))),
            "fresh": views.make_form_token(),
            "not a number": views.signing.TimestampSigner(salt="comments.form").sign("soon"),
            "a number": 5,
        }
        for label, token in tokens.items():
            self.assertPending(self.submit(form_token=token))
            self.assertEqual(Comment.objects.count(), 0, label)

    def test_the_form_token_must_be_three_seconds_old(self):
        now = 1_800_000_000
        token = views.make_form_token(now)
        with mock.patch.object(views, "_now", return_value=now + 2.9):
            self.submit(form_token=token)
            self.assertEqual(Comment.objects.count(), 0)
        with mock.patch.object(views, "_now", return_value=now + 3):
            self.submit(form_token=token)
            self.assertEqual(Comment.objects.count(), 1)

    def test_the_form_token_never_expires(self):
        token = views.make_form_token(time.time() - 400 * 24 * 3600)
        self.submit(form_token=token)
        self.assertEqual(Comment.objects.count(), 1)

    def test_a_token_from_the_listing_works_after_a_pause(self):
        token = self.client.get(COMMENTS, {"post": self.post.pk}).json()["form_token"]
        with mock.patch.object(views, "_now", return_value=time.time() + 60):
            self.submit(form_token=token)
        self.assertEqual(Comment.objects.count(), 1)

    def test_broken_json_is_answered_like_a_bot(self):
        response = self.client.post(COMMENTS, "{nope", content_type="application/json")
        self.assertPending(response)
        self.assertEqual(Comment.objects.count(), 0)

    @override_settings(COMMENTS_POST_LIMIT=2)
    def test_the_throttle_is_per_ip_and_counts_every_post(self):
        self.assertEqual(self.submit().status_code, 200)
        self.assertEqual(self.submit(website="bot").status_code, 200)  # Bots count too.
        response = self.submit()
        self.assertEqual((response.status_code, response.json()), (429, {"status": "rate_limited"}))
        self.assertEqual(Comment.objects.count(), 1)
        elsewhere = self.submit(extra={"HTTP_X_REAL_IP": "203.0.113.9"})
        self.assertEqual(elsewhere.status_code, 200)

    @override_settings(COMMENTS_POST_LIMIT=1)
    def test_the_throttle_comes_first_and_form_posts_are_sent_back_to_the_post(self):
        self.submit()
        response = self.client.post(COMMENTS, self.payload())
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], f"{POST_URL}?comment=rate_limited#comment-form")
        # Even an unknown post answers 429 once over the limit.
        self.assertEqual(self.submit(post=999999).status_code, 429)

    @override_settings(COMMENTS_POST_LIMIT=1)
    def test_the_comment_throttle_is_separate_from_the_newsletter_one(self):
        self.post_json("/api/v2/newsletter/subscribe/", {"email": "a@example.com"})
        self.assertEqual(self.submit().status_code, 200)

    def test_a_closed_post_or_site_refuses_with_a_403_and_stores_nothing(self):
        BlogPage.objects.filter(pk=self.post.pk).update(allow_comments=False)
        for _ in range(2):
            response = self.submit()
            self.assertEqual((response.status_code, response.json()), (403, {"status": "closed"}))
        BlogPage.objects.filter(pk=self.post.pk).update(allow_comments=True)
        set_comment_settings(enabled=False)
        self.assertEqual(self.submit().status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_a_missing_or_unpublished_post_is_a_404(self):
        draft = make_post("A Draft", datetime.date(2024, 6, 1))
        Page.objects.filter(pk=draft.pk).update(live=False)
        for value in (draft.pk, 999999, "abc", None, HomePage.objects.get().pk):
            response = self.submit(post=value)
            self.assertEqual(
                (response.status_code, response.json()), (404, {"status": "not_found"}), value
            )

    def test_a_bot_is_not_told_that_the_post_does_not_exist(self):
        self.assertPending(self.submit(post=999999, website="x"))

    def test_other_methods_are_405(self):
        self.assertEqual(self.client.delete(COMMENTS).status_code, 405)


@override_settings(
    FRONTEND_URL="https://example.org", AKISMET_API_KEY="a-key", COMMENTS_POST_LIMIT=1000
)
class AkismetPostTests(CommentsTestCase):
    """What posting does with Akismet's verdict, and what Akismet is told."""

    def payload(self, **fields):
        return {
            "post": self.post.pk,
            "name": "Ann",
            "email": "ann@example.com",
            "body": "Nice post",
            "website": "",
            "form_token": old_token(),
            **fields,
        }

    def submit(self, extra=None, **fields):
        return self.post_json(COMMENTS, self.payload(**fields), **(extra or {}))

    def test_a_comment_akismet_likes_waits_for_review_marked_not_spam(self):
        with FakeAkismet("ham") as akismet:
            response = self.submit()
        self.assertEqual((response.status_code, response.json()), (200, {"status": "pending"}))
        comment = Comment.objects.get()
        self.assertEqual((comment.status, comment.spam_check), (Comment.PENDING, Comment.HAM))
        self.assertEqual(len(akismet.checks), 1)

    def test_a_comment_akismet_calls_spam_is_stored_as_spam_but_the_answer_is_the_same(self):
        with FakeAkismet("spam"):
            response = self.submit(notify_replies=True)
        self.assertEqual((response.status_code, response.json()), (200, {"status": "pending"}))
        comment = Comment.objects.get()
        self.assertEqual((comment.status, comment.spam_check), (Comment.SPAM, Comment.SPAM))
        self.assertEqual(mail.outbox, [])

    def test_blatant_spam_is_not_stored_at_all(self):
        with FakeAkismet("discard"):
            response = self.submit()
        self.assertEqual((response.status_code, response.json()), (200, {"status": "pending"}))
        self.assertEqual(Comment.objects.count(), 0)

    def test_an_akismet_problem_never_blocks_the_comment(self):
        problems = {
            "network down": FakeAkismet(error=httpx.ConnectError("no route")),
            "timeout": FakeAkismet(error=httpx.ReadTimeout("too slow")),
            "server error": FakeAkismet(status=500, body="oops"),
            "wrong key": FakeAkismet(body="invalid"),
            "gibberish": FakeAkismet(body="maybe"),
        }
        for label, fake in problems.items():
            Comment.objects.all().delete()
            cache.clear()
            with fake, self.assertLogs("comments.spam", "WARNING") as logs:
                response = self.submit()
            self.assertEqual(response.status_code, 200, label)
            comment = Comment.objects.get()
            self.assertEqual((comment.status, comment.spam_check), ("pending", "unchecked"), label)
            self.assertIn("Akismet check failed", logs.output[0])

    @override_settings(AKISMET_API_KEY="")
    def test_without_a_key_nothing_is_sent_and_the_comment_is_unchecked(self):
        with FakeAkismet("spam") as akismet:
            self.submit()
        self.assertEqual(akismet.requests, [])
        self.assertEqual(Comment.objects.get().spam_check, Comment.UNCHECKED)

    def test_akismet_is_told_about_the_comment(self):
        Page.objects.filter(pk=self.post.pk).update(
            last_published_at=datetime.datetime(2024, 5, 4, 8, 30, tzinfo=datetime.UTC)
        )
        with FakeAkismet("ham") as akismet:
            self.submit(
                extra={
                    "HTTP_X_REAL_IP": "203.0.113.7",
                    "HTTP_USER_AGENT": "Mozilla/5.0 Test",
                    "HTTP_REFERER": f"https://example.org{POST_URL}",
                },
                name="Ann Lee",
                body="Great\n\npost",
            )
        [params] = akismet.checks
        date = params.pop("comment_date_gmt")
        self.assertEqual(
            params,
            {
                "api_key": "a-key",
                "blog": "https://example.org",
                "user_ip": "203.0.113.7",
                "user_agent": "Mozilla/5.0 Test",
                "referrer": f"https://example.org{POST_URL}",
                "permalink": f"https://example.org{POST_URL}",
                "comment_type": "comment",
                "comment_author": "Ann Lee",
                "comment_author_email": "ann@example.com",
                "comment_content": "Great\n\npost",
                "comment_post_modified_gmt": "2024-05-04T08:30:00+00:00",
                "blog_lang": "en",
                "blog_charset": "UTF-8",
                "honeypot_field_name": "website",
            },
        )
        self.assertTrue(datetime.datetime.fromisoformat(date).tzinfo is not None)
        self.assertLess(
            abs(datetime.datetime.fromisoformat(date) - timezone.now()),
            datetime.timedelta(minutes=1),
        )

    def test_a_reply_is_sent_as_a_reply(self):
        top = approved(self.post)
        with FakeAkismet("ham") as akismet:
            self.submit(parent=top.pk)
        self.assertEqual(akismet.checks[0]["comment_type"], "reply")

    @override_settings(AKISMET_TEST_MODE=True)
    def test_test_mode_says_so(self):
        with FakeAkismet("ham") as akismet:
            self.submit()
        self.assertEqual(akismet.checks[0]["is_test"], "1")

    def test_there_is_no_test_flag_outside_test_mode(self):
        with FakeAkismet("ham") as akismet:
            self.submit()
        self.assertNotIn("is_test", akismet.checks[0])

    def test_one_request_per_comment_and_no_key_check(self):
        with FakeAkismet("ham") as akismet:
            self.submit()
            self.submit(body="Another")
        self.assertEqual([endpoint for endpoint, _ in akismet.requests], ["comment-check"] * 2)

    def test_the_client_is_quick_and_says_who_it_is(self):
        with FakeAkismet("ham") as akismet:
            self.submit()
        [kwargs] = akismet.clients
        self.assertLessEqual(kwargs["timeout"], 5)
        self.assertTrue(kwargs["headers"]["User-Agent"].startswith("akismet.py/"))

    def test_the_visitors_details_are_kept_for_reports(self):
        with FakeAkismet("ham"):
            self.submit(
                extra={
                    "HTTP_X_REAL_IP": "203.0.113.7",
                    "HTTP_USER_AGENT": "Agent",
                    "HTTP_REFERER": "https://example.org/x",
                }
            )
        comment = Comment.objects.get()
        self.assertEqual(
            (comment.ip_address, comment.user_agent, comment.referrer),
            ("203.0.113.7", "Agent", "https://example.org/x"),
        )

    def test_very_long_details_are_cut(self):
        with FakeAkismet("ham"):
            self.submit(extra={"HTTP_USER_AGENT": "A" * 900, "HTTP_REFERER": "R" * 900})
        comment = Comment.objects.get()
        self.assertEqual((len(comment.user_agent), len(comment.referrer)), (500, 500))

    def test_an_address_that_is_not_one_is_not_sent_or_kept(self):
        with FakeAkismet("spam") as akismet:
            self.submit(extra={"HTTP_X_REAL_IP": "not-an-ip"})
        self.assertEqual(akismet.requests, [])
        comment = Comment.objects.get()
        self.assertEqual((comment.status, comment.ip_address), (Comment.PENDING, None))

    def test_spam_is_not_checked_for_posts_that_fail_validation(self):
        with FakeAkismet("spam") as akismet:
            self.submit(email="nope")
        self.assertEqual(akismet.requests, [])


# Akismet module


@override_settings(FRONTEND_URL="https://example.org", AKISMET_API_KEY="a-key")
class SpamModuleTests(CommentsTestCase):
    def comment(self, **fields):
        fields = {
            "ip_address": "203.0.113.7",
            "user_agent": "Agent",
            "referrer": "https://example.org/x",
            "status": Comment.PENDING,
            **fields,
        }
        return make_comment(self.post, name="Ann", body="Spammy words", **fields)

    def test_the_client_is_built_from_our_settings_not_the_environment(self):
        with spam.client() as akismet_client:
            self.assertEqual(akismet_client._config, ("a-key", "https://example.org"))

    def test_reporting_spam(self):
        comment = self.comment()
        with FakeAkismet() as akismet:
            self.assertTrue(spam.report_spam(comment))
        [(endpoint, params)] = akismet.reports
        self.assertEqual(endpoint, "submit-spam")
        self.assertEqual(params["user_ip"], "203.0.113.7")
        self.assertEqual(params["user_agent"], "Agent")
        self.assertEqual(params["referrer"], "https://example.org/x")
        self.assertEqual(params["comment_content"], "Spammy words")
        self.assertEqual(params["comment_author"], "Ann")
        self.assertEqual(params["comment_author_email"], "ann@example.com")
        self.assertEqual(params["comment_type"], "comment")
        self.assertEqual(params["permalink"], f"https://example.org{POST_URL}")
        self.assertEqual(params["honeypot_field_name"], "website")
        self.assertEqual(
            datetime.datetime.fromisoformat(params["comment_date_gmt"]), comment.created_at
        )

    def test_reporting_ham(self):
        comment = self.comment(parent=approved(self.post))
        with FakeAkismet() as akismet:
            self.assertTrue(spam.report_ham(comment))
        [(endpoint, params)] = akismet.reports
        self.assertEqual((endpoint, params["comment_type"]), ("submit-ham", "reply"))

    @override_settings(AKISMET_TEST_MODE=True)
    def test_reports_carry_the_test_flag_in_test_mode(self):
        with FakeAkismet() as akismet:
            spam.report_spam(self.comment())
        self.assertEqual(akismet.reports[0][1]["is_test"], "1")

    @override_settings(AKISMET_API_KEY="")
    def test_no_reports_without_a_key(self):
        with FakeAkismet() as akismet:
            self.assertFalse(spam.report_spam(self.comment()))
            self.assertFalse(spam.report_ham(self.comment()))
        self.assertEqual(akismet.requests, [])

    def test_no_reports_without_a_stored_address(self):
        with FakeAkismet() as akismet:
            self.assertFalse(spam.report_spam(self.comment(ip_address=None)))
        self.assertEqual(akismet.requests, [])

    def test_report_errors_are_logged_not_raised(self):
        comment = self.comment()
        for fake in (
            FakeAkismet(error=httpx.ConnectError("down")),
            FakeAkismet(body="invalid"),
            FakeAkismet(status=503, body=""),
        ):
            with fake, self.assertLogs("comments.spam", "WARNING"):
                self.assertFalse(spam.report_spam(comment))

    def test_check_without_a_key_or_an_address_asks_nobody(self):
        request = mock.Mock(headers={}, META={"REMOTE_ADDR": "203.0.113.7"})
        with FakeAkismet("spam") as akismet:
            with override_settings(AKISMET_API_KEY=""):
                self.assertEqual(spam.check(self.comment(), request, self.post), "unchecked")
            request.META["REMOTE_ADDR"] = ""
            self.assertEqual(spam.check(self.comment(), request, self.post), "unchecked")
        self.assertEqual(akismet.requests, [])

    def test_check_answers(self):
        request = mock.Mock(headers={}, META={"REMOTE_ADDR": "203.0.113.7"})
        answers = {}
        for verdict in ("ham", "spam", "discard"):
            with FakeAkismet(verdict):
                answers[verdict] = spam.check(self.comment(), request, self.post)
        self.assertEqual(answers, {"ham": "ham", "spam": "spam", "discard": "discard"})


# Moderation


@override_settings(FRONTEND_URL="https://example.org", DEFAULT_FROM_EMAIL="Blog <news@example.org>")
class ModerationTests(CommentsTestCase):
    def test_approving_makes_it_public_and_stamps_the_time(self):
        comment = make_comment(self.post)
        self.assertEqual(moderation.approve(comment), [])
        comment.refresh_from_db()
        self.assertEqual(comment.status, Comment.APPROVED)
        self.assertLess(timezone.now() - comment.reviewed_at, datetime.timedelta(minutes=1))
        self.assertEqual(mail.outbox, [])

    def test_approving_an_approved_comment_does_nothing(self):
        comment = approved(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        with mock.patch.object(moderation.spam, "report_ham") as report_ham:
            self.assertEqual(moderation.approve(comment), [])
        comment.refresh_from_db()
        self.assertIsNone(comment.reviewed_at)
        self.assertEqual(mail.outbox, [])
        report_ham.assert_not_called()

    def test_asking_for_alerts_sends_one_confirmation_when_the_comment_goes_live(self):
        comment = make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        moderation.approve(comment)
        [message] = mail.outbox
        self.assertEqual(message.to, ["ann@example.com"])
        self.assertEqual(message.subject, "Your comment on “Hello World” is live")
        self.assertIn(
            f"https://example.org/comments/alerts/confirm/?token={comment.token}", message.body
        )
        comment.refresh_from_db()
        self.assertEqual(comment.reply_alerts, Comment.ALERTS_REQUESTED)  # Not on until the click.

    def test_no_confirmation_unless_asked_for_or_for_the_authors_own_comments_or_without_email(
        self,
    ):
        moderation.approve(make_comment(self.post))
        moderation.approve(make_comment(self.post, reply_alerts=Comment.ALERTS_ON))
        moderation.approve(
            make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED, is_author=True)
        )
        moderation.approve(make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED, email=""))
        self.assertEqual(mail.outbox, [])

    def test_a_reply_alert_goes_to_the_author_of_the_comment_answered(self):
        parent = approved(self.post, name="Ann", reply_alerts=Comment.ALERTS_ON)
        reply = make_comment(self.post, name="Bob", email="bob@example.com", parent=parent)
        self.assertEqual(moderation.approve(reply), [])
        [message] = mail.outbox
        self.assertEqual(message.to, ["ann@example.com"])
        self.assertEqual(message.subject, "Bob replied to your comment on “Hello World”")
        self.assertIn(reply.public_url(), message.body)

    def test_a_reply_alert_needs_every_condition(self):
        def reply_to(parent, **fields):
            fields = {"name": "Bob", "email": "bob@example.com", **fields}
            return make_comment(self.post, parent=parent, **fields)

        on = Comment.ALERTS_ON
        cases = {
            "alerts off": approved(self.post, reply_alerts=Comment.ALERTS_OFF),
            "alerts only requested": approved(self.post, reply_alerts=Comment.ALERTS_REQUESTED),
            "parent is the author": approved(self.post, reply_alerts=on, is_author=True),
            "parent not approved": make_comment(self.post, reply_alerts=on),
            "parent is spam": make_comment(self.post, reply_alerts=on, status=Comment.SPAM),
            "no email": approved(self.post, reply_alerts=on, email=""),
        }
        for label, parent in cases.items():
            moderation.approve(reply_to(parent))
            self.assertEqual(mail.outbox, [], label)

        replying_to_themselves = approved(self.post, reply_alerts=on, email="bob@example.com")
        moderation.approve(reply_to(replying_to_themselves))
        self.assertEqual(mail.outbox, [])

    def test_the_owners_reply_is_marked_as_the_authors(self):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        reply = make_comment(
            self.post,
            name="Prabuddh Mathur",
            email="owner@example.com",
            parent=parent,
            is_author=True,
        )
        moderation.approve(reply)
        [message] = mail.outbox
        self.assertIn("Prabuddh Mathur (author)", message.body)

    def test_a_reply_that_asks_for_alerts_to_a_parent_with_alerts_on_sends_both_emails(self):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        reply = make_comment(
            self.post,
            name="Bob",
            email="bob@example.com",
            parent=parent,
            reply_alerts=Comment.ALERTS_REQUESTED,
        )
        moderation.approve(reply)
        self.assertEqual(
            sorted(m.to[0] for m in mail.outbox), ["ann@example.com", "bob@example.com"]
        )

    def test_a_failing_mail_server_is_a_warning_and_the_comment_is_still_approved(self):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        reply = make_comment(
            self.post,
            name="Bob",
            email="bob@example.com",
            parent=parent,
            reply_alerts=Comment.ALERTS_REQUESTED,
        )
        with override_settings(EMAIL_BACKEND="comments.tests.FailingBackend"):
            warnings = moderation.approve(reply)
        self.assertEqual(len(warnings), 2)
        self.assertIn("bob@example.com", warnings[0])
        self.assertIn("ann@example.com", warnings[1])
        self.assertIn("mail server is down", warnings[0])
        reply.refresh_from_db()
        self.assertEqual(reply.status, Comment.APPROVED)

    def test_the_emails_use_the_connection_of_the_action(self):
        comment = make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        effects = moderation.Effects()
        with mock.patch.object(moderation.emails, "build_alerts_confirmation") as build:
            moderation.approve(comment, effects)
        build.assert_called_once_with(comment, effects.connection)

    def test_actions_that_send_no_email_never_connect_to_the_mail_server(self):
        waiting = make_comment(self.post)
        live = approved(self.post)
        CountingBackend.opened = 0
        with override_settings(EMAIL_BACKEND="comments.tests.CountingBackend"):
            moderation.run("approve", [waiting])
            moderation.run("like", [live])
            moderation.run("spam", [live])
        self.assertEqual(CountingBackend.opened, 0)

    def test_once_the_mail_server_cannot_be_reached_the_action_stops_trying(self):
        comments = [
            make_comment(
                self.post, email=f"c{n}@example.com", reply_alerts=Comment.ALERTS_REQUESTED
            )
            for n in range(3)
        ]
        UnreachableBackend.attempts = 0
        with override_settings(EMAIL_BACKEND="comments.tests.UnreachableBackend"):
            outcome = moderation.run("approve", comments)
        self.assertEqual(UnreachableBackend.attempts, 1)
        self.assertEqual(outcome.changed, 3)
        self.assertEqual(len(outcome.warnings), 3)
        for n, warning in enumerate(outcome.warnings):
            self.assertIn(f"c{n}@example.com", warning)
            self.assertIn("couldn't be reached", warning)

    def test_once_akismet_fails_the_action_stops_telling_it(self):
        comments = [approved(self.post) for _ in range(3)]
        with mock.patch.object(moderation.spam, "report_spam", return_value=False) as report:
            outcome = moderation.run("spam", comments)
        self.assertEqual(report.call_count, 1)
        self.assertEqual(outcome.changed, 3)

    def test_akismet_without_details_to_report_is_not_a_failure(self):
        comments = [approved(self.post) for _ in range(3)]
        with mock.patch.object(moderation.spam, "report_spam", return_value=None) as report:
            moderation.run("spam", comments)
        self.assertEqual(report.call_count, 3)

    def test_approving_something_akismet_called_spam_tells_akismet(self):
        for fields in (
            {"status": Comment.SPAM},
            {"status": Comment.SPAM, "spam_check": Comment.SPAM},
            {"status": Comment.PENDING, "spam_check": Comment.SPAM},
        ):
            comment = make_comment(self.post, **fields)
            with mock.patch.object(moderation.spam, "report_ham") as report_ham:
                moderation.approve(comment)
            report_ham.assert_called_once_with(comment)

    def test_approving_an_ordinary_comment_tells_akismet_nothing(self):
        for check in (Comment.UNCHECKED, Comment.HAM):
            comment = make_comment(self.post, spam_check=check)
            with mock.patch.object(moderation.spam, "report_ham") as report_ham:
                moderation.approve(comment)
            report_ham.assert_not_called()

    def test_marking_spam_hides_the_comment_and_tells_akismet(self):
        comment = approved(self.post)
        with mock.patch.object(moderation.spam, "report_spam") as report_spam:
            moderation.mark_spam(comment)
        comment.refresh_from_db()
        self.assertEqual(comment.status, Comment.SPAM)
        self.assertIsNotNone(comment.reviewed_at)
        report_spam.assert_called_once_with(comment)

    def test_akismet_is_not_told_about_what_it_already_called_spam_or_twice(self):
        comment = make_comment(self.post, spam_check=Comment.SPAM)
        with mock.patch.object(moderation.spam, "report_spam") as report_spam:
            moderation.mark_spam(comment)
            moderation.mark_spam(make_comment(self.post, status=Comment.SPAM))
        report_spam.assert_not_called()
        self.assertEqual(comment.status, Comment.SPAM)

    def test_only_approved_comments_can_be_liked(self):
        comment = make_comment(self.post)
        self.assertFalse(moderation.set_liked(comment, True))
        comment.refresh_from_db()
        self.assertFalse(comment.liked)
        comment.status = Comment.APPROVED
        comment.save()
        self.assertTrue(moderation.set_liked(comment, True))
        self.assertFalse(moderation.set_liked(comment, True))
        comment.refresh_from_db()
        self.assertTrue(comment.liked)
        self.assertTrue(moderation.set_liked(comment, False))
        comment.refresh_from_db()
        self.assertFalse(comment.liked)

    def test_the_owner_answers_a_comment(self):
        parent = approved(self.post)
        user = get_user_model().objects.create_user("owner", "owner@example.com", "pw")
        reply, warnings = moderation.author_reply(parent, "Thanks!", user)
        self.assertEqual(warnings, [])
        reply.refresh_from_db()
        self.assertEqual(
            (reply.status, reply.is_author, reply.parent, reply.root_id, reply.post),
            (Comment.APPROVED, True, parent, parent.pk, self.post),
        )
        self.assertEqual(
            (reply.name, reply.email, reply.body, reply.spam_check, reply.reply_alerts),
            ("Prabuddh Mathur", "owner@example.com", "Thanks!", "unchecked", "off"),
        )
        self.assertIsNotNone(reply.reviewed_at)

    def test_the_owners_name_comes_from_the_author_settings(self):
        site = Site.objects.get(is_default_site=True)
        author = AuthorSettings.for_site(site)
        author.author_name = "P. Mathur"
        author.save()
        user = get_user_model().objects.create_user("owner", "", "pw")
        reply, _ = moderation.author_reply(approved(self.post), "Hi", user)
        self.assertEqual((reply.name, reply.email), ("P. Mathur", ""))

    def test_answering_a_waiting_comment_approves_it_first_with_its_emails(self):
        parent = make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        user = get_user_model().objects.create_user("owner", "owner@example.com", "pw")
        reply, warnings = moderation.author_reply(parent, "Thanks!", user)
        parent.refresh_from_db()
        self.assertEqual(parent.status, Comment.APPROVED)
        [message] = mail.outbox  # Only the confirmation: alerts aren't on yet.
        self.assertEqual(message.subject, "Your comment on “Hello World” is live")
        self.assertEqual(warnings, [])

    def test_answering_a_comment_with_alerts_on_sends_the_alert(self):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        user = get_user_model().objects.create_user("owner", "owner@example.com", "pw")
        moderation.author_reply(parent, "Thanks!", user)
        [message] = mail.outbox
        self.assertEqual(message.to, ["ann@example.com"])
        self.assertIn("(author)", message.body)

    def test_a_reply_to_a_reply_joins_the_thread(self):
        top = approved(self.post)
        reply = approved(self.post, parent=top)
        user = get_user_model().objects.create_user("owner", "owner@example.com", "pw")
        answer, _ = moderation.author_reply(reply, "Yes", user)
        self.assertEqual(answer.root_id, top.pk)

    def test_the_owner_cannot_answer_spam(self):
        user = get_user_model().objects.create_user("owner", "owner@example.com", "pw")
        with self.assertRaises(ValueError):
            moderation.author_reply(make_comment(self.post, status=Comment.SPAM), "Hi", user)
        self.assertEqual(Comment.objects.count(), 1)

    def test_a_failing_mail_server_does_not_stop_the_owners_reply(self):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        user = get_user_model().objects.create_user("owner", "owner@example.com", "pw")
        with override_settings(EMAIL_BACKEND="comments.tests.FailingBackend"):
            reply, warnings = moderation.author_reply(parent, "Thanks!", user)
        self.assertEqual(len(warnings), 1)
        self.assertTrue(Comment.objects.filter(pk=reply.pk, status=Comment.APPROVED).exists())

    def test_run_counts_what_changed_and_skips_the_rest(self):
        waiting, done = make_comment(self.post), approved(self.post)
        outcome = moderation.run("approve", [waiting, done])
        self.assertEqual((outcome.changed, outcome.warnings), (1, []))
        self.assertEqual(moderation.run("spam", [waiting, done]).changed, 2)
        self.assertEqual(moderation.run("spam", [done]).changed, 0)
        self.assertEqual(moderation.run("like", [done]).changed, 0)  # Spam now.
        fresh = approved(self.post)
        self.assertEqual(moderation.run("like", [fresh]).changed, 1)
        self.assertEqual(moderation.run("unlike", [fresh]).changed, 1)
        self.assertEqual(moderation.run("unlike", [fresh]).changed, 0)
        with self.assertRaises(ValueError):
            moderation.run("explode", [fresh])

    def test_run_collects_the_warnings_of_every_comment(self):
        comments = [
            make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED) for _ in range(2)
        ]
        with override_settings(EMAIL_BACKEND="comments.tests.FailingBackend"):
            outcome = moderation.run("approve", comments)
        self.assertEqual((outcome.changed, len(outcome.warnings)), (2, 2))


# Alert endpoints


class AlertEndpointTests(CommentsTestCase):
    def setUp(self):
        super().setUp()
        self.comment = approved(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        self.token = self.comment.token

    def state(self):
        self.comment.refresh_from_db()
        return self.comment.reply_alerts

    def test_confirm_turns_alerts_on(self):
        response = self.post_json(CONFIRM, {"token": self.token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "on", "post": {"title": "Hello World", "url": POST_URL}},
        )
        self.assertEqual(self.state(), Comment.ALERTS_ON)

    def test_confirm_is_idempotent_and_also_works_from_a_form(self):
        self.post_json(CONFIRM, {"token": self.token})
        response = self.client.post(CONFIRM, {"token": self.token})
        self.assertEqual((response.status_code, response.json()["status"]), (200, "on"))
        self.assertEqual(self.state(), Comment.ALERTS_ON)

    def test_confirm_with_an_unknown_missing_or_odd_token_is_a_404(self):
        for token in ("nope", "", None, 5, ["x"]):
            response = self.post_json(CONFIRM, {"token": token})
            self.assertEqual(
                (response.status_code, response.json()), (404, {"status": "invalid_token"}), token
            )
        self.assertEqual(self.post_json(CONFIRM, {}).status_code, 404)
        self.assertEqual(self.state(), Comment.ALERTS_REQUESTED)

    def test_confirm_only_allows_post(self):
        self.assertEqual(self.client.get(CONFIRM, {"token": self.token}).status_code, 405)
        self.assertEqual(self.state(), Comment.ALERTS_REQUESTED)

    def test_stop_turns_alerts_off(self):
        Comment.objects.filter(pk=self.comment.pk).update(reply_alerts=Comment.ALERTS_ON)
        response = self.post_json(STOP, {"token": self.token})
        self.assertEqual(
            (response.status_code, response.json()),
            (200, {"status": "off", "post": {"title": "Hello World", "url": POST_URL}}),
        )
        self.assertEqual(self.state(), Comment.ALERTS_OFF)

    def test_stop_is_idempotent_and_takes_the_token_from_the_query_too(self):
        self.client.post(
            f"{STOP}?token={self.token}", json.dumps({}), content_type="application/json"
        )
        response = self.client.post(f"{STOP}?token={self.token}", content_type="application/json")
        self.assertEqual((response.status_code, response.json()["status"]), (200, "off"))
        self.assertEqual(self.state(), Comment.ALERTS_OFF)

    def test_a_form_post_is_redirected_to_the_page_that_shows_the_outcome(self):
        response = self.client.post(STOP, {"token": self.token})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], "/comments/alerts/stop/?status=off")
        self.assertEqual(self.state(), Comment.ALERTS_OFF)
        response = self.client.post(STOP, {"token": "nope"})
        self.assertEqual(response["Location"], "/comments/alerts/stop/?status=invalid_token")

    def test_the_one_click_post_from_a_mail_client_gets_json(self):
        Comment.objects.filter(pk=self.comment.pk).update(reply_alerts=Comment.ALERTS_ON)
        response = self.client.post(
            f"{STOP}?token={self.token}",
            "List-Unsubscribe=One-Click",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual((response.status_code, response.json()["status"]), (200, "off"))
        self.assertEqual(self.state(), Comment.ALERTS_OFF)
        response = self.client.post(
            f"{STOP}?token=nope",
            "List-Unsubscribe=One-Click",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(
            (response.status_code, response.json()), (404, {"status": "invalid_token"})
        )

    def test_get_redirects_to_the_page_and_changes_nothing(self):
        Comment.objects.filter(pk=self.comment.pk).update(reply_alerts=Comment.ALERTS_ON)
        response = self.client.get(STOP, {"token": self.token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/comments/alerts/stop/?token={self.token}")
        self.assertEqual(self.client.get(STOP)["Location"], "/comments/alerts/stop/")
        self.assertEqual(self.state(), Comment.ALERTS_ON)

    def test_an_unknown_token_is_a_404_for_json(self):
        response = self.post_json(STOP, {"token": "nope"})
        self.assertEqual(
            (response.status_code, response.json()), (404, {"status": "invalid_token"})
        )
        self.assertEqual(self.post_json(STOP, {}).status_code, 404)

    def test_other_methods_are_405(self):
        self.assertEqual(self.client.put(STOP).status_code, 405)
        self.assertEqual(self.client.delete(CONFIRM).status_code, 405)


# Emails


@override_settings(FRONTEND_URL="https://example.org", DEFAULT_FROM_EMAIL="Blog <news@example.org>")
class EmailTests(CommentsTestCase):
    def test_the_confirmation_has_text_and_html_with_absolute_links(self):
        comment = approved(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        message = emails.build_alerts_confirmation(comment)
        self.assertEqual(message.subject, "Your comment on “Hello World” is live")
        self.assertEqual(message.to, ["ann@example.com"])
        self.assertEqual(message.from_email, "Blog <news@example.org>")
        confirm = f"https://example.org/comments/alerts/confirm/?token={comment.token}"
        comment_url = f"https://example.org{POST_URL}#comment-{comment.pk}"
        html = html_of(message)
        for part in (message.body, html):
            self.assertIn(confirm, part)
            self.assertIn(comment_url, part)
            self.assertIn("You asked to get an email when someone replies", part)
            self.assertIn("If you didn't write this comment, ignore this email", part)
        self.assertIn("Email me replies", html)
        self.assertIn(f'href="{confirm}"', html)
        self.assertNotIn('href="/', html)
        self.assertNotIn("List-Unsubscribe", message.extra_headers)

    def test_message_ids_use_the_site_domain(self):
        comment = approved(self.post)
        for message in (emails.build_alerts_confirmation(comment), self.reply_message()):
            self.assertRegex(message.message()["Message-ID"], r"^<[^@>]+@example\.org>$")

    def reply_message(self, body="Thanks, Ann!", **fields):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        fields = {"name": "Bob", "email": "bob@example.com", **fields}
        reply = approved(self.post, parent=parent, body=body, **fields)
        self.parent, self.reply = parent, reply
        return emails.build_reply_alert(reply)

    def test_the_reply_alert_goes_to_the_parents_author_with_a_stop_link(self):
        message = self.reply_message()
        self.assertEqual(message.subject, "Bob replied to your comment on “Hello World”")
        self.assertEqual(message.to, ["ann@example.com"])
        token = self.parent.token
        self.assertEqual(
            message.extra_headers["List-Unsubscribe"],
            f"<https://example.org/api/v2/comments/alerts/stop/?token={token}>",
        )
        self.assertEqual(
            message.extra_headers["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click"
        )
        reply_url = f"https://example.org{POST_URL}#comment-{self.reply.pk}"
        stop = f"https://example.org/comments/alerts/stop/?token={token}"
        html = html_of(message)
        for part in (message.body, html):
            self.assertIn(reply_url, part)
            self.assertIn(stop, part)
            self.assertIn("Thanks, Ann!", part)
            self.assertIn("you asked for replies to your comment on example.org", part)
        self.assertIn("Read the reply", html)
        self.assertNotIn('href="/', html)
        self.assertNotIn("(author)", message.body)

    def test_the_owner_is_marked_as_the_author(self):
        message = self.reply_message(name="Prabuddh Mathur", is_author=True)
        self.assertIn("Prabuddh Mathur (author) replied", message.body)
        self.assertIn("(author)", html_of(message))

    def test_what_a_reader_wrote_is_escaped_in_the_html_and_not_in_the_text(self):
        message = self.reply_message(name="<b>Bob</b>", body="<script>alert(1)</script> & more")
        html = html_of(message)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>Bob</b>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; more", html)
        self.assertIn("&lt;b&gt;Bob&lt;/b&gt;", html)
        self.assertIn("<script>alert(1)</script> & more", message.body)

    def test_line_breaks_are_kept(self):
        message = self.reply_message(body="One\nTwo\n\nThree")
        self.assertIn("One<br>Two<br><br>Three", html_of(message))
        self.assertIn("One\nTwo\n\nThree", message.body)

    def test_a_long_reply_is_cut_at_a_thousand_characters(self):
        message = self.reply_message(body="x" * 1000)
        self.assertIn("x" * 1000, message.body)
        self.assertNotIn("…", message.body)
        message = self.reply_message(body="y" * 1500)
        self.assertIn("y" * 1000 + "…", message.body)
        self.assertNotIn("y" * 1001, message.body)
        self.assertIn("y" * 1000 + "…", html_of(message))

    def test_subjects_stay_on_one_line(self):
        self.post.title = "Two\nlines"
        comment = approved(self.post)
        self.assertEqual(
            emails.build_alerts_confirmation(comment).subject, "Your comment on “Two lines” is live"
        )
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        reply = approved(self.post, parent=parent, name="Bob\nBob")
        self.assertEqual(
            emails.build_reply_alert(reply).subject,
            "Bob Bob replied to your comment on “Two lines”",
        )

    def test_the_connection_is_passed_on(self):
        connection = mail.get_connection()
        comment = approved(self.post)
        self.assertIs(emails.build_alerts_confirmation(comment, connection).connection, connection)
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        reply = approved(self.post, parent=parent)
        self.assertIs(emails.build_reply_alert(reply, connection).connection, connection)


# Housekeeping


class HousekeepingTests(CommentsTestCase):
    def aged(self, days, **fields):
        comment = make_comment(
            self.post,
            ip_address="203.0.113.7",
            user_agent="Agent",
            referrer="https://x.y",
            **fields,
        )
        when = timezone.now() - datetime.timedelta(days=days)
        Comment.objects.filter(pk=comment.pk).update(created_at=when)
        if comment.status != Comment.PENDING or fields.get("reviewed_at"):
            Comment.objects.filter(pk=comment.pk).update(reviewed_at=when)
        return comment

    def test_old_spam_is_deleted_and_the_rest_is_kept(self):
        old_spam = self.aged(31, status=Comment.SPAM)
        new_spam = self.aged(29, status=Comment.SPAM)
        old_approved = self.aged(400, status=Comment.APPROVED)
        old_pending = self.aged(400)
        counts = housekeeping.purge()
        self.assertEqual(counts["spam_deleted"], 1)
        self.assertFalse(Comment.objects.filter(pk=old_spam.pk).exists())
        for comment in (new_spam, old_approved, old_pending):
            self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_spam_the_owner_marked_counts_from_when_it_was_marked(self):
        # Posted long ago, marked as spam today: there is still a month to change one's mind.
        marked_today = self.aged(400, status=Comment.SPAM)
        Comment.objects.filter(pk=marked_today.pk).update(reviewed_at=timezone.now())
        housekeeping.purge()
        self.assertTrue(Comment.objects.filter(pk=marked_today.pk).exists())

    def test_spam_akismet_caught_counts_from_when_it_was_posted(self):
        old = self.aged(31, status=Comment.SPAM, spam_check=Comment.SPAM)
        new = self.aged(29, status=Comment.SPAM, spam_check=Comment.SPAM)
        Comment.objects.filter(pk__in=[old.pk, new.pk]).update(reviewed_at=None)
        housekeeping.purge()
        self.assertFalse(Comment.objects.filter(pk=old.pk).exists())
        self.assertTrue(Comment.objects.filter(pk=new.pk).exists())

    def test_visitor_details_of_reviewed_comments_are_cleared_after_a_month(self):
        old = self.aged(40, status=Comment.APPROVED)
        recent = self.aged(10, status=Comment.APPROVED)
        waiting = self.aged(40)
        counts = housekeeping.purge()
        self.assertEqual(counts["details_cleared"], 1)
        old.refresh_from_db()
        self.assertEqual((old.ip_address, old.user_agent, old.referrer), (None, "", ""))
        for comment in (recent, waiting):
            comment.refresh_from_db()
            self.assertEqual(comment.ip_address, "203.0.113.7")
            self.assertEqual(comment.user_agent, "Agent")

    def test_the_comment_itself_is_untouched_when_its_details_are_cleared(self):
        old = self.aged(40, status=Comment.APPROVED, liked=True)
        housekeeping.purge()
        old.refresh_from_db()
        self.assertEqual(
            (old.status, old.liked, old.body, old.email),
            ("approved", True, "Hello there", "ann@example.com"),
        )

    def test_clearing_is_not_counted_twice(self):
        self.aged(40, status=Comment.APPROVED)
        self.assertEqual(housekeeping.purge()["details_cleared"], 1)
        self.assertEqual(housekeeping.purge(), {"spam_deleted": 0, "details_cleared": 0})

    def test_purge_can_be_run_for_another_moment(self):
        self.aged(5, status=Comment.SPAM)
        later = timezone.now() + datetime.timedelta(days=40)
        self.assertEqual(housekeeping.purge(now=later)["spam_deleted"], 1)

    def test_the_command_reports_what_it_did(self):
        self.aged(31, status=Comment.SPAM)
        self.aged(31, status=Comment.APPROVED)
        out = StringIO()
        call_command("comments_cleanup", stdout=out)
        self.assertIn("Deleted 1 spam comment(s)", out.getvalue())
        self.assertIn("cleared the visitor details of 1 comment(s)", out.getvalue())
        self.assertEqual(Comment.objects.count(), 1)


class WorkerHousekeepingTests(CommentsTestCase):
    def test_the_worker_runs_the_housekeeping(self):
        old = make_comment(self.post, status=Comment.SPAM)
        Comment.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=45)
        )
        with self.assertLogs("newsletter.worker", "INFO") as logs:
            call_command("newsletter_worker", "--once", stdout=StringIO())
        self.assertEqual(Comment.objects.count(), 0)
        self.assertTrue(any("Comment housekeeping: 1 spam deleted" in line for line in logs.output))

    def test_it_says_nothing_when_there_was_nothing_to_do(self):
        make_comment(self.post)
        with self.assertLogs("newsletter.worker", "INFO") as logs:
            call_command("newsletter_worker", "--once", stdout=StringIO())
        self.assertFalse(any("housekeeping" in line for line in logs.output))

    def test_it_runs_at_most_once_an_hour(self):
        command = newsletter_worker.Command()
        clock = [1000.0]
        counts = {"spam_deleted": 0, "details_cleared": 0}
        with (
            mock.patch.object(newsletter_worker, "purge", return_value=counts) as purge,
            mock.patch.object(newsletter_worker.time, "monotonic", lambda: clock[0]),
        ):
            command.run_housekeeping()
            clock[0] += 3599
            command.run_housekeeping()
            self.assertEqual(purge.call_count, 1)
            clock[0] += 2
            command.run_housekeeping()
            self.assertEqual(purge.call_count, 2)
            command.run_housekeeping()
            self.assertEqual(purge.call_count, 2)

    def test_a_failure_is_logged_and_the_worker_carries_on(self):
        command = newsletter_worker.Command()
        with (
            mock.patch.object(
                newsletter_worker, "purge", side_effect=RuntimeError("no such table")
            ),
            self.assertLogs("newsletter.worker", "ERROR") as logs,
        ):
            command.run_housekeeping()
        self.assertTrue(any("no such table" in line for line in logs.output))


# Deploy check


class DeployCheckTests(TestCase):
    def test_warns_without_an_akismet_key(self):
        with override_settings(AKISMET_API_KEY=""):
            [warning] = check_akismet_configured(None)
        self.assertEqual(warning.id, "comments.W001")
        self.assertIn("Akismet isn't configured", warning.msg)
        self.assertIn("without a spam check", warning.msg)

    def test_quiet_with_a_key(self):
        with override_settings(AKISMET_API_KEY="a-key"):
            self.assertEqual(check_akismet_configured(None), [])

    def test_the_check_is_registered_for_deploy(self):
        self.assertIn(check_akismet_configured, checks_registry.registry.deployment_checks)


# Wagtail admin


@override_settings(FRONTEND_URL="https://example.org")
class AdminTestCase(CommentsTestCase):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
        self.client.force_login(self.admin)

    def user_with(self, *codenames, username="editor"):
        user = get_user_model().objects.create_user(username, f"{username}@example.com", "pw")
        for codename in ("access_admin", *codenames):
            # Wagtail's own page comments have permissions with the same names.
            app_label = "comments" if codename.endswith("_comment") else "wagtailadmin"
            user.user_permissions.add(
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
            )
        return user

    def messages(self, response):
        """The messages shown on the page a followed redirect ended on."""
        return [str(message) for message in response.context["messages"]]

    def action(self, comment, name, follow=True, **extra):
        return self.client.post(f"/admin/comments/{comment.pk}/{name}/", follow=follow, **extra)

    def status_of(self, comment):
        comment.refresh_from_db()
        return comment.status


class AdminListingTests(AdminTestCase):
    def test_login_and_permission_are_required(self):
        comment = make_comment(self.post)
        self.client.logout()
        for url in ("/admin/comments/", f"/admin/comments/edit/{comment.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(
            self.client.post(f"/admin/comments/{comment.pk}/approve/").status_code, 302
        )
        self.assertEqual(self.status_of(comment), Comment.PENDING)

        self.client.force_login(self.user_with())
        self.assertRedirects(
            self.client.get("/admin/comments/"), "/admin/", fetch_redirect_response=False
        )
        self.assertRedirects(
            self.action(comment, "approve", follow=False), "/admin/", fetch_redirect_response=False
        )
        self.assertRedirects(
            self.client.get(f"/admin/comments/{comment.pk}/reply/"),
            "/admin/",
            fetch_redirect_response=False,
        )
        self.assertEqual(self.status_of(comment), Comment.PENDING)

        self.client.force_login(self.user_with("change_comment", username="mod"))
        self.assertEqual(self.client.get("/admin/comments/").status_code, 200)
        self.assertEqual(self.action(comment, "approve", follow=False).status_code, 302)
        self.assertEqual(self.status_of(comment), Comment.APPROVED)

    def test_the_listing_shows_waiting_comments_first_then_the_newest(self):
        now = timezone.now()
        old_waiting = make_comment(self.post, name="Old waiting")
        new_waiting = make_comment(self.post, name="New waiting")
        old_done = approved(self.post, name="Old approved")
        new_junk = make_comment(self.post, name="New junk", status=Comment.SPAM)
        for offset, comment in enumerate([old_waiting, old_done, new_waiting, new_junk]):
            set_created(comment, now + datetime.timedelta(minutes=offset))
        response = self.client.get("/admin/comments/")
        titles = [c.name for c in response.context["object_list"]]
        self.assertEqual(titles, ["New waiting", "Old waiting", "New junk", "Old approved"])

    def test_the_listing_shows_what_the_owner_needs(self):
        top = approved(self.post, name="Ann", body="First line\nsecond", liked=True)
        make_comment(self.post, name="Bob", email="bob@example.com", parent=top, spam_check="ham")
        content = self.client.get("/admin/comments/").content.decode()
        for text in (
            "First line second",
            "Ann",
            "bob@example.com",
            "Hello World",
            "Approved",
            "Waiting for review",
            "Not spam",
            "Not checked",
            "✓",
            "Comments",
            "bulk-action",
        ):
            self.assertIn(text, content)
        self.assertNotIn("Add comment", content)

    def test_filters_and_search(self):
        a = approved(self.post, name="Ann", email="ann@example.com", body="alpha")
        b = make_comment(self.post, name="Bob", email="bob@example.org", body="beta")
        c = make_comment(
            self.post,
            name="Cat",
            email="cat@example.net",
            status=Comment.SPAM,
            spam_check="spam",
            body="gamma",
        )
        other = approved(
            make_post("Other", datetime.date(2024, 5, 4)),
            name="Dan",
            email="dan@example.com",
            body="delta",
        )

        def names(query):
            response = self.client.get(f"/admin/comments/?{query}")
            self.assertEqual(response.status_code, 200)
            return sorted(c.name for c in response.context["object_list"])

        self.assertEqual(names("status=pending"), ["Bob"])
        self.assertEqual(names("status=spam"), ["Cat"])
        self.assertEqual(names("spam_check=spam"), ["Cat"])
        self.assertEqual(names(f"post={other.post.pk}"), ["Dan"])
        self.assertEqual(names("q=bob@example.org"), ["Bob"])
        self.assertEqual(names("q=Ann"), ["Ann"])
        self.assertEqual(names("q=gamma"), ["Cat"])
        self.assertEqual(sorted([a.name, b.name, c.name, other.name]), ["Ann", "Bob", "Cat", "Dan"])

    def test_the_columns_can_be_sorted(self):
        make_comment(self.post, name="Zed")
        make_comment(self.post, name="Amy")
        for key in (
            "name",
            "email",
            "status",
            "spam_check",
            "liked",
            "created_at",
            "body",
            "post__title",
        ):
            for sign in ("", "-"):
                response = self.client.get(f"/admin/comments/?ordering={sign}{key}")
                self.assertEqual(response.status_code, 200, key)
        response = self.client.get("/admin/comments/?ordering=name")
        self.assertEqual([c.name for c in response.context["object_list"]], ["Amy", "Zed"])

    def test_the_listing_is_a_few_queries_whatever_the_number_of_comments(self):
        for n in range(3):
            make_comment(self.post, name=f"A{n}")
        with CaptureQueriesContext(connection) as few:
            self.client.get("/admin/comments/")
        for n in range(10):
            make_comment(self.post, name=f"B{n}")
        with CaptureQueriesContext(connection) as many:
            self.client.get("/admin/comments/")
        self.assertEqual(len(few), len(many))

    def test_row_buttons_depend_on_the_status(self):
        waiting = make_comment(self.post, name="Waiting")
        done = approved(self.post, name="Done")
        liked = approved(self.post, name="Liked", liked=True)
        junk = make_comment(self.post, name="Junk", status=Comment.SPAM)
        content = self.client.get("/admin/comments/").content.decode()

        def has(comment, name):
            return f'data-w-action-url-value="/admin/comments/{comment.pk}/{name}/"' in content

        self.assertEqual(
            [has(waiting, n) for n in ("approve", "spam", "like", "unlike")],
            [True, True, False, False],
        )
        self.assertEqual(
            [has(done, n) for n in ("approve", "spam", "like", "unlike")],
            [False, True, True, False],
        )
        self.assertEqual(
            [has(liked, n) for n in ("approve", "spam", "like", "unlike")],
            [False, True, False, True],
        )
        self.assertEqual(
            [has(junk, n) for n in ("approve", "spam", "like", "unlike")],
            [True, False, False, False],
        )
        for comment, expected in ((waiting, True), (done, True), (liked, True), (junk, False)):
            self.assertEqual(f"/admin/comments/{comment.pk}/reply/" in content, expected)
        for comment in (waiting, done, liked, junk):
            self.assertIn(f"/admin/comments/delete/{comment.pk}/", content)

    def test_a_user_who_cannot_change_comments_gets_no_action_buttons(self):
        comment = make_comment(self.post)
        self.client.force_login(self.user_with("delete_comment"))
        content = self.client.get("/admin/comments/").content.decode()
        self.assertNotIn(f"/admin/comments/{comment.pk}/approve/", content)
        self.assertIn(f"/admin/comments/delete/{comment.pk}/", content)

    def test_the_menu_shows_how_many_are_waiting(self):
        self.assertContains(self.client.get("/admin/"), '"label": "Comments"', html=False)
        make_comment(self.post)
        make_comment(self.post)
        approved(self.post)
        self.assertContains(self.client.get("/admin/"), "Comments (2)")

    def test_the_menu_item_is_for_people_who_can_moderate(self):
        item = CommentsMenuItem("Comments", "/admin/comments/")
        request = mock.Mock(user=self.user_with())
        self.assertFalse(item.is_shown(request))
        request.user = self.user_with("delete_comment", username="d")
        self.assertTrue(item.is_shown(request))
        request.user = self.user_with("change_comment", username="c")
        self.assertTrue(item.is_shown(request))

    def test_only_change_and_delete_permissions_are_offered_for_groups(self):
        codenames = set(
            Comment.snippet_viewset.get_permissions_to_register().values_list("codename", flat=True)
        )
        self.assertEqual(codenames, {"change_comment", "delete_comment"})

    def test_nobody_can_add_a_comment_by_hand(self):
        policy = CommentPermissionPolicy(Comment)
        self.assertFalse(policy.user_has_permission(self.admin, "add"))
        self.assertTrue(policy.user_has_permission(self.admin, "change"))
        self.assertEqual(list(policy.users_with_any_permission(["add"])), [])
        self.assertIn(self.admin, policy.users_with_any_permission(["add", "change"]))
        response = self.client.post(
            "/admin/comments/add/", {"name": "x", "body": "y", "liked": "on"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)


class AdminActionTests(AdminTestCase):
    def test_approve(self):
        comment = make_comment(self.post)
        response = self.action(comment, "approve")
        self.assertEqual(response.redirect_chain, [("/admin/comments/", 302)])
        self.assertEqual(self.status_of(comment), Comment.APPROVED)
        self.assertIn("Approved 1 comment.", self.messages(response)[0])

    def test_the_action_returns_to_the_page_it_was_clicked_on(self):
        comment = make_comment(self.post)
        response = self.action(
            comment, "approve", follow=False, data={"next": "/admin/comments/?status=pending"}
        )
        self.assertRedirects(
            response, "/admin/comments/?status=pending", fetch_redirect_response=False
        )

    def test_an_outside_address_is_not_followed(self):
        comment = make_comment(self.post)
        response = self.action(
            comment, "approve", follow=False, data={"next": "https://evil.example/"}
        )
        self.assertEqual(response["Location"], "/admin/comments/")

    def test_approving_sends_the_alert_confirmation_and_shows_mail_trouble_as_a_warning(self):
        comment = make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        self.action(comment, "approve")
        [message] = mail.outbox
        self.assertEqual(message.to, ["ann@example.com"])

        other = make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED)
        with override_settings(EMAIL_BACKEND="comments.tests.FailingBackend"):
            response = self.action(other, "approve")
        self.assertEqual(self.status_of(other), Comment.APPROVED)
        texts = self.messages(response)
        self.assertEqual(len(texts), 2)
        self.assertIn("Approved 1 comment.", texts[0])
        self.assertIn("be sent", texts[1])
        self.assertIn("mail server is down", texts[1])

    def test_mark_as_spam_tells_akismet(self):
        comment = approved(self.post)
        with mock.patch.object(moderation.spam, "report_spam") as report_spam:
            response = self.action(comment, "spam")
        self.assertEqual(self.status_of(comment), Comment.SPAM)
        self.assertIn("Marked 1 comment as spam.", self.messages(response)[0])
        report_spam.assert_called_once()

    def test_like_and_unlike(self):
        comment = approved(self.post)
        response = self.action(comment, "like")
        self.assertIn("Liked 1 comment.", self.messages(response)[0])
        comment.refresh_from_db()
        self.assertTrue(comment.liked)
        response = self.action(comment, "unlike")
        self.assertIn("Removed your like from 1 comment.", self.messages(response)[0])
        comment.refresh_from_db()
        self.assertFalse(comment.liked)

    def test_an_action_that_does_nothing_says_so(self):
        waiting, done = make_comment(self.post), approved(self.post)
        self.assertIn("can be liked", self.messages(self.action(waiting, "like"))[0])
        self.assertIn("already approved", self.messages(self.action(done, "approve"))[0])
        self.assertIn("is not liked", self.messages(self.action(done, "unlike"))[0])
        junk = make_comment(self.post, status=Comment.SPAM)
        self.assertIn("already marked as spam", self.messages(self.action(junk, "spam"))[0])

    def test_actions_only_take_post_and_known_comments(self):
        comment = make_comment(self.post)
        self.assertEqual(self.client.get(f"/admin/comments/{comment.pk}/approve/").status_code, 405)
        self.assertEqual(self.status_of(comment), Comment.PENDING)
        self.assertEqual(self.client.post("/admin/comments/999999/approve/").status_code, 404)
        self.assertEqual(
            self.client.post(f"/admin/comments/{comment.pk}/explode/").status_code, 404
        )

    def test_an_action_needs_the_change_permission(self):
        comment = make_comment(self.post)
        self.client.force_login(self.user_with("delete_comment"))
        self.action(comment, "approve")
        self.action(comment, "spam")
        self.assertEqual(self.status_of(comment), Comment.PENDING)


class AdminBulkTests(AdminTestCase):
    def url(self, action, *comments):
        ids = "&".join(f"id={c.pk}" for c in comments)
        return f"/admin/bulk/comments/comment/{action}/?{ids}&next=/admin/comments/"

    def test_the_three_actions_are_available_for_comments(self):
        actions = {
            action.action_type: action
            for action in bulk_action_registry.get_bulk_actions_for_model("comments", "comment")
        }
        self.assertEqual(sorted(actions), ["approve", "delete", "spam"])
        self.assertIs(actions["delete"], DeleteCommentsBulkAction)
        content = self.client.get("/admin/comments/").content.decode()
        for name in ("approve", "spam", "delete"):
            self.assertIn(f"/admin/bulk/comments/comment/{name}/", content)

    def test_approving_several_comments(self):
        comments = [make_comment(self.post, name=f"C{n}") for n in range(3)]
        page = self.client.get(self.url("approve", *comments))
        self.assertContains(page, "Approve 3 comments?")
        for comment in comments:
            self.assertContains(page, comment.name)
        self.assertContains(page, "Yes, approve")
        self.assertEqual([self.status_of(c) for c in comments], ["pending"] * 3)

        response = self.client.post(self.url("approve", *comments), follow=True)
        self.assertEqual(response.redirect_chain, [("/admin/comments/", 302)])
        self.assertEqual([self.status_of(c) for c in comments], ["approved"] * 3)
        self.assertIn("Approved 3 comments.", self.messages(response)[0])

    def test_the_emails_of_a_bulk_approval_share_one_connection(self):
        comments = [
            make_comment(
                self.post, email=f"c{n}@example.com", reply_alerts=Comment.ALERTS_REQUESTED
            )
            for n in range(3)
        ]
        CountingBackend.opened = 0
        with override_settings(EMAIL_BACKEND="comments.tests.CountingBackend"):
            self.client.post(self.url("approve", *comments))
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(CountingBackend.opened, 1)

    def test_a_bulk_approval_shows_each_mail_problem(self):
        comments = [
            make_comment(self.post, reply_alerts=Comment.ALERTS_REQUESTED) for _ in range(2)
        ]
        with override_settings(EMAIL_BACKEND="comments.tests.FailingBackend"):
            response = self.client.post(self.url("approve", *comments), follow=True)
        self.assertEqual([self.status_of(c) for c in comments], ["approved"] * 2)
        self.assertEqual(len(self.messages(response)), 3)

    def test_marking_several_comments_as_spam(self):
        comments = [approved(self.post, name=f"C{n}") for n in range(2)]
        self.assertContains(self.client.get(self.url("spam", *comments)), "Yes, mark as spam")
        with mock.patch.object(moderation.spam, "report_spam") as report_spam:
            response = self.client.post(self.url("spam", *comments), follow=True)
        self.assertEqual([self.status_of(c) for c in comments], ["spam"] * 2)
        self.assertIn("Marked 2 comments as spam.", self.messages(response)[0])
        self.assertEqual(report_spam.call_count, 2)

    def test_a_bulk_action_that_changes_nothing_says_so(self):
        done = approved(self.post)
        response = self.client.post(self.url("approve", done), follow=True)
        self.assertIn("already approved", self.messages(response)[0])

    def test_deleting_says_the_replies_go_too_and_does_it(self):
        top = approved(self.post, name="Top")
        reply = approved(self.post, name="Reply", parent=top)
        other = approved(self.post, name="Other")
        page = self.client.get(self.url("delete", top, other))
        self.assertContains(page, "Replies to these comments are deleted too.")
        response = self.client.post(self.url("delete", top, other))
        self.assertRedirects(response, "/admin/comments/", fetch_redirect_response=False)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertFalse(Comment.objects.filter(pk=reply.pk).exists())

    def test_one_comment_in_the_delete_page_reads_in_the_singular(self):
        page = self.client.get(self.url("delete", make_comment(self.post)))
        self.assertContains(page, "Replies to this comment are deleted too.")

    def test_select_all_in_listing_means_the_filtered_list_not_every_comment(self):
        waiting = [make_comment(self.post, name=f"Waiting{n}") for n in range(3)]
        live = approved(self.post, name="Live")
        junk = make_comment(self.post, name="Junk", status=Comment.SPAM)
        base = "/admin/bulk/comments/comment"

        page = self.client.get(f"{base}/approve/?status=pending&id=all&next=/admin/comments/")
        self.assertContains(page, "Approve 3 comments?")
        self.assertNotContains(page, "Live")
        self.client.post(f"{base}/approve/?status=pending&id=all&next=/admin/comments/")
        self.assertEqual([self.status_of(c) for c in waiting], ["approved"] * 3)
        self.assertEqual(self.status_of(junk), Comment.SPAM)

        # A search narrows it too, and so do several filters together.
        self.client.post(f"{base}/spam/?status=approved&q=Waiting1&id=all")
        self.assertEqual(
            [self.status_of(c) for c in [*waiting, live]],
            ["approved", "spam", "approved", "approved"],
        )

        # The delete action takes the same list: only the spam goes.
        self.client.post(f"{base}/delete/?status=spam&id=all")
        self.assertEqual(
            sorted(Comment.objects.values_list("name", flat=True)), ["Live", "Waiting0", "Waiting2"]
        )

        # With no filter it is every comment, as the link says.
        page = self.client.get(f"{base}/approve/?id=all")
        self.assertContains(page, "Approve 3 comments?")

    def test_someone_who_cannot_change_comments_cannot_approve_in_bulk(self):
        comment = make_comment(self.post)
        self.client.force_login(self.user_with("delete_comment"))
        page = self.client.get(self.url("approve", comment))
        self.assertContains(page, "don't have permission")
        self.client.post(self.url("approve", comment))
        self.assertEqual(self.status_of(comment), Comment.PENDING)

    def test_someone_who_cannot_delete_comments_cannot_delete_in_bulk(self):
        comment = make_comment(self.post)
        self.client.force_login(self.user_with("change_comment"))
        self.client.post(self.url("delete", comment))
        self.assertEqual(Comment.objects.count(), 1)


class AdminEditTests(AdminTestCase):
    def test_the_form_has_the_name_text_and_heart_but_not_the_status(self):
        comment = approved(self.post, name="Ann", body="Hello")
        response = self.client.get(f"/admin/comments/edit/{comment.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(response.context["form"].fields), ["body", "liked", "name"])

    def test_it_shows_what_cannot_be_edited(self):
        top = approved(self.post, name="Ann", body="The first")
        reply = make_comment(
            self.post,
            name="Bob",
            email="bob@example.com",
            parent=top,
            spam_check="ham",
            reply_alerts=Comment.ALERTS_REQUESTED,
        )
        content = self.client.get(f"/admin/comments/edit/{reply.pk}/").content.decode()
        for text in (
            "bob@example.com",
            "Waiting for review",
            "Not spam",
            "Asked for, not confirmed",
            "Ann: The first",
            f"https://example.org{POST_URL}#comment-{reply.pk}",
            "Hello World",
            f"/admin/comments/{reply.pk}/approve/",
            f"/admin/comments/{reply.pk}/spam/",
            f"/admin/comments/{reply.pk}/reply/",
        ):
            self.assertIn(text, content)
        self.assertNotIn(f"/admin/comments/{reply.pk}/like/", content)

    def test_saving_changes_the_name_text_and_heart_and_nothing_else(self):
        comment = make_comment(self.post, name="Ann", body="Hello")
        response = self.client.post(
            f"/admin/comments/edit/{comment.pk}/",
            {"name": "Ann L.", "body": "Hello, edited", "liked": "on", "status": "approved"},
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(
            (comment.name, comment.body, comment.liked), ("Ann L.", "Hello, edited", True)
        )
        self.assertEqual(comment.status, Comment.PENDING)
        self.assertEqual(mail.outbox, [])

    def test_deleting_one_comment_says_when_replies_go_too(self):
        top = approved(self.post)
        approved(self.post, parent=top)
        alone = approved(self.post)
        self.assertContains(
            self.client.get(f"/admin/comments/delete/{top.pk}/"),
            "The replies to it are deleted too.",
        )
        self.assertNotContains(
            self.client.get(f"/admin/comments/delete/{alone.pk}/"), "replies to it"
        )
        self.client.post(f"/admin/comments/delete/{top.pk}/")
        self.assertEqual(list(Comment.objects.all()), [alone])


class AdminReplyTests(AdminTestCase):
    def url(self, comment):
        return f"/admin/comments/{comment.pk}/reply/"

    def test_the_page_shows_the_comment_and_what_it_answers(self):
        top = approved(self.post, name="Ann", body="The first")
        reply = make_comment(self.post, name="Bob", body="Line one\nLine two", parent=top)
        response = self.client.get(self.url(reply))
        self.assertContains(response, "Publish reply")
        self.assertContains(response, "Bob")
        self.assertContains(response, "Line one")
        self.assertContains(response, "In reply to Ann: The first")
        self.assertContains(response, "also approves it")

    def test_an_approved_comment_has_no_approval_note(self):
        self.assertNotContains(self.client.get(self.url(approved(self.post))), "also approves it")

    def test_publishing_a_reply(self):
        parent = approved(self.post, name="Ann")
        response = self.client.post(
            self.url(parent), {"body": "  Thanks, Ann!  \r\n\r\n\r\nBye"}, follow=True
        )
        self.assertEqual(response.redirect_chain, [("/admin/comments/", 302)])
        reply = Comment.objects.get(is_author=True)
        self.assertEqual(
            (reply.parent, reply.status, reply.body, reply.name, reply.email),
            (
                parent,
                Comment.APPROVED,
                "Thanks, Ann!\n\nBye",
                "Prabuddh Mathur",
                "admin@example.com",
            ),
        )
        self.assertIn("Your reply to Ann is published.", self.messages(response)[0])

    def test_replying_to_a_waiting_comment_approves_it(self):
        parent = make_comment(self.post, name="Ann", reply_alerts=Comment.ALERTS_REQUESTED)
        response = self.client.post(self.url(parent), {"body": "Thanks"}, follow=True)
        self.assertEqual(self.status_of(parent), Comment.APPROVED)
        self.assertIn("the comment is approved", self.messages(response)[0])
        [message] = mail.outbox
        self.assertEqual(message.to, ["ann@example.com"])

    def test_mail_trouble_is_shown_after_the_success_message(self):
        parent = approved(self.post, reply_alerts=Comment.ALERTS_ON)
        with override_settings(EMAIL_BACKEND="comments.tests.FailingBackend"):
            response = self.client.post(self.url(parent), {"body": "Thanks"}, follow=True)
        texts = self.messages(response)
        self.assertEqual(len(texts), 2)
        self.assertIn("published", texts[0])
        self.assertIn("be sent", texts[1])
        self.assertEqual(Comment.objects.filter(is_author=True).count(), 1)

    def test_a_bad_reply_shows_the_problem_and_creates_nothing(self):
        parent = approved(self.post)
        for body, problem in (
            ("", "Please write a reply."),
            (" \n ", "Please write a reply."),
            ("x" * 5001, "at most 5,000"),
        ):
            response = self.client.post(self.url(parent), {"body": body})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, problem)
        self.assertEqual(Comment.objects.count(), 1)

    def test_spam_cannot_be_answered(self):
        junk = make_comment(self.post, status=Comment.SPAM)
        response = self.client.get(self.url(junk), follow=True)
        self.assertEqual(response.redirect_chain, [("/admin/comments/", 302)])
        self.assertIn("marked as spam", self.messages(response)[0])
        self.client.post(self.url(junk), {"body": "Hi"})
        self.assertEqual(Comment.objects.count(), 1)

    def test_it_returns_to_where_it_came_from(self):
        parent = approved(self.post)
        response = self.client.post(
            self.url(parent), {"body": "Hi", "next": "/admin/comments/?status=pending"}
        )
        self.assertEqual(response["Location"], "/admin/comments/?status=pending")
        page = self.client.get(self.url(parent) + "?next=/admin/comments/?status=pending")
        self.assertContains(page, 'name="next"')

    def test_unknown_comments_are_a_404(self):
        self.assertEqual(self.client.get("/admin/comments/999999/reply/").status_code, 404)

    def test_the_reply_shows_on_the_public_page_under_the_comment(self):
        parent = approved(self.post, name="Ann")
        self.client.post(self.url(parent), {"body": "Thanks"})
        [thread] = self.client.get(COMMENTS, {"post": self.post.pk}).json()["comments"]
        [reply] = thread["replies"]
        self.assertEqual(
            (reply["name"], reply["is_author"], reply["body"]), ("Prabuddh Mathur", True, "Thanks")
        )


class AdminDashboardTests(AdminTestCase):
    def test_the_dashboard_counts_the_comments_waiting_for_review(self):
        self.assertNotContains(self.client.get("/admin/"), "waiting for review")
        make_comment(self.post)
        content = self.client.get("/admin/").content.decode()
        self.assertIn("1 comment", content)
        self.assertIn("waiting for review", content)
        self.assertIn('href="/admin/comments/?status=pending"', content)
        make_comment(self.post)
        approved(self.post)
        make_comment(self.post, status=Comment.SPAM)
        self.assertIn("2 comments", self.client.get("/admin/").content.decode())

    def test_it_is_hidden_from_people_who_cannot_moderate(self):
        make_comment(self.post)
        self.client.force_login(self.user_with())
        self.assertNotContains(self.client.get("/admin/"), "waiting for review")

    def test_the_summary_item(self):
        make_comment(self.post)
        request = mock.Mock(user=self.admin)
        item = PendingCommentsSummaryItem(request)
        self.assertTrue(item.is_shown())
        context = item.get_context_data({})
        self.assertEqual(context["count"], 1)
        self.assertEqual(context["url"], "/admin/comments/?status=pending")


class AdminSettingsTests(AdminTestCase):
    def test_the_settings_page_changes_what_the_public_api_says(self):
        site = Site.objects.get(is_default_site=True)
        url = f"/admin/settings/comments/commentsettings/{site.pk}/"
        page = self.client.get(url)
        self.assertContains(page, "Liked by Prabuddh")
        self.assertContains(page, "Turning this off hides them everywhere")
        response = self.client.post(url, {"enabled": "", "like_label": "Hearted by me"})
        self.assertEqual(response.status_code, 302)
        data = self.client.get(COMMENTS, {"post": self.post.pk}).json()
        self.assertEqual(
            (data["enabled"], data["open"], data["like_label"]), (False, False, "Hearted by me")
        )

    def test_the_settings_are_in_the_settings_menu_as_comments(self):
        self.assertContains(self.client.get("/admin/"), "/admin/settings/comments/commentsettings/")

    def test_posts_have_the_checkbox_in_their_settings_tab(self):
        page = self.client.get(f"/admin/pages/{self.post.pk}/edit/")
        self.assertContains(page, 'name="allow_comments"')
        self.assertContains(page, "Let readers comment on this post.")

    def test_wagtails_own_editor_comments_are_off(self):
        page = self.client.get(f"/admin/pages/{self.post.pk}/edit/")
        self.assertNotContains(page, "w-comments")
        self.assertNotContains(page, "data-comments-enabled")


class GroupPermissionTests(AdminTestCase):
    def test_a_group_can_be_given_the_comment_permissions(self):
        group = Group.objects.create(name="Comment moderators")
        group.permissions.add(Permission.objects.get(codename="access_admin"))
        group.permissions.add(
            Permission.objects.get(content_type__app_label="comments", codename="change_comment")
        )
        user = get_user_model().objects.create_user("mod", "mod@example.com", "pw")
        user.groups.add(group)
        comment = make_comment(self.post)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/admin/comments/").status_code, 200)
        self.action(comment, "approve")
        self.assertEqual(self.status_of(comment), Comment.APPROVED)


class UrlsTests(TestCase):
    def test_the_comment_endpoints_win_over_the_wagtail_api(self):
        from django.urls import resolve

        for path, name in (
            ("/api/v2/comments/", "comments"),
            ("/api/v2/comments/alerts/confirm/", "comments_alerts_confirm"),
            ("/api/v2/comments/alerts/stop/", "comments_alerts_stop"),
        ):
            self.assertEqual(resolve(path).url_name, name)
