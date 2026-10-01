import datetime
import json
import logging
import tempfile
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.cache import cache
from django.core.mail.backends import locmem
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site

from blog.tests import make_post
from core.models import SiteSettings
from home.models import HomePage

from . import emails, sending
from .checks import check_email_configured
from .management.commands import newsletter_worker
from .models import Delivery, Issue, Subscriber
from .sending import BatchResult
from .wagtail_hooks import offer_to_email_post

# Expected failures are logged by the code under test; keep them out of the test output.
logging.getLogger("newsletter").addHandler(logging.NullHandler())

SUBSCRIBE = "/api/v2/newsletter/subscribe/"
CONFIRM = "/api/v2/newsletter/confirm/"
UNSUBSCRIBE = "/api/v2/newsletter/unsubscribe/"


def make_subscriber(email="reader@example.com", status=Subscriber.SUBSCRIBED):
    return Subscriber.objects.create(email=email, status=status)


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


class NewsletterTestCase(TestCase):
    def setUp(self):
        cache.clear()  # The signup throttle lives in the cache.

    def post_json(self, url, data, **extra):
        return self.client.post(url, json.dumps(data), content_type="application/json", **extra)


@override_settings(FRONTEND_URL="https://example.org")
class SubscribeTests(NewsletterTestCase):
    def subscribe(self, email="Reader@Example.com", headers=None, **fields):
        data = {"email": email, "website": "", **fields}
        return self.post_json(SUBSCRIBE, data, **(headers or {}))

    def test_new_address_gets_a_pending_subscriber_and_a_confirmation(self):
        response = self.subscribe()
        self.assertEqual((response.status_code, response.json()), (200, {"status": "ok"}))
        subscriber = Subscriber.objects.get()
        self.assertEqual(subscriber.status, Subscriber.PENDING)
        self.assertIsNotNone(subscriber.confirmation_sent_at)
        [message] = mail.outbox
        self.assertEqual(message.to, ["reader@example.com"])
        self.assertIn(
            f"https://example.org/newsletter/confirm/?token={subscriber.token}", message.body
        )

    def test_email_is_stripped_and_lower_cased(self):
        self.subscribe("  Reader@Example.COM ")
        self.assertEqual(Subscriber.objects.get().email, "reader@example.com")
        self.subscribe("reader@example.com")  # The same person: no second row.
        self.assertEqual(Subscriber.objects.count(), 1)

    def test_invalid_email_is_a_400(self):
        for bad in ["", "nope", "a@b", "x" * 250 + "@example.com", None, 5]:
            response = self.subscribe(bad)
            self.assertEqual(
                (response.status_code, response.json()), (400, {"status": "invalid_email"}), bad
            )
        self.assertEqual(Subscriber.objects.count(), 0)
        self.assertEqual(mail.outbox, [])

    def test_honeypot_says_ok_and_does_nothing(self):
        response = self.subscribe(website="http://spam.example")
        self.assertEqual((response.status_code, response.json()), (200, {"status": "ok"}))
        self.assertEqual(Subscriber.objects.count(), 0)
        self.assertEqual(mail.outbox, [])

    def test_already_subscribed_sends_nothing_but_looks_the_same(self):
        make_subscriber()
        response = self.subscribe()
        self.assertEqual((response.status_code, response.json()), (200, {"status": "ok"}))
        self.assertEqual(mail.outbox, [])

    def test_pending_within_the_cooldown_sends_nothing(self):
        subscriber = make_subscriber(status=Subscriber.PENDING)
        subscriber.confirmation_sent_at = timezone.now() - datetime.timedelta(minutes=5)
        subscriber.save()
        self.assertEqual(self.subscribe().json(), {"status": "ok"})
        self.assertEqual(mail.outbox, [])

    def test_pending_after_the_cooldown_resends(self):
        subscriber = make_subscriber(status=Subscriber.PENDING)
        subscriber.confirmation_sent_at = timezone.now() - datetime.timedelta(minutes=11)
        subscriber.save()
        self.assertEqual(self.subscribe().json(), {"status": "ok"})
        self.assertEqual(len(mail.outbox), 1)
        subscriber.refresh_from_db()
        self.assertGreater(
            subscriber.confirmation_sent_at, timezone.now() - datetime.timedelta(minutes=1)
        )

    def test_unsubscribed_goes_back_to_pending_with_the_same_token(self):
        subscriber = make_subscriber(status=Subscriber.UNSUBSCRIBED)
        token = subscriber.token
        self.assertEqual(self.subscribe().json(), {"status": "ok"})
        subscriber.refresh_from_db()
        self.assertEqual((subscriber.status, subscriber.token), (Subscriber.PENDING, token))
        self.assertEqual(len(mail.outbox), 1)

    def test_smtp_failure_is_a_503_and_leaves_the_row_pending_to_retry(self):
        with (
            mock.patch("django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("down")),
            self.assertLogs("newsletter.views", "ERROR"),
        ):
            response = self.subscribe()
        self.assertEqual((response.status_code, response.json()), (503, {"status": "email_failed"}))
        subscriber = Subscriber.objects.get()
        self.assertEqual(subscriber.status, Subscriber.PENDING)
        self.assertIsNone(subscriber.confirmation_sent_at)
        # Trying again resends, with no cooldown in the way.
        self.assertEqual(self.subscribe().json(), {"status": "ok"})
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(NEWSLETTER_SUBSCRIBE_LIMIT=2)
    def test_throttle_is_per_ip(self):
        for n in range(2):
            self.assertEqual(self.subscribe(f"a{n}@example.com").status_code, 200)
        response = self.subscribe("a3@example.com")
        self.assertEqual((response.status_code, response.json()), (429, {"status": "rate_limited"}))
        self.assertFalse(Subscriber.objects.filter(email="a3@example.com").exists())
        # Another visitor (Caddy's X-Real-IP) isn't affected.
        self.assertEqual(
            self.subscribe("b@example.com", {"HTTP_X_REAL_IP": "203.0.113.9"}).status_code, 200
        )

    def test_form_post_redirects_with_303(self):
        response = self.client.post(SUBSCRIBE, {"email": "reader@example.com", "website": ""})
        self.assertEqual(
            (response.status_code, response["Location"]), (303, "/newsletter/?status=ok")
        )
        response = self.client.post(SUBSCRIBE, {"email": "bad"})
        self.assertEqual(response["Location"], "/newsletter/?status=invalid_email")
        self.assertEqual(len(mail.outbox), 1)

    def test_form_post_reports_failures(self):
        with (
            mock.patch("django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("down")),
            self.assertLogs("newsletter.views", "ERROR"),
        ):
            response = self.client.post(SUBSCRIBE, {"email": "reader@example.com"})
        self.assertEqual(response["Location"], "/newsletter/?status=email_failed")

    def test_only_post_is_allowed(self):
        self.assertEqual(self.client.get(SUBSCRIBE).status_code, 405)

    def test_broken_json_is_an_invalid_email(self):
        response = self.client.post(SUBSCRIBE, "{nope", content_type="application/json")
        self.assertEqual(response.status_code, 400)


class ConfirmTests(NewsletterTestCase):
    def confirm(self, token):
        return self.post_json(CONFIRM, {"token": token})

    def test_pending_becomes_subscribed(self):
        subscriber = make_subscriber(status=Subscriber.PENDING)
        response = self.confirm(subscriber.token)
        self.assertEqual(
            (response.status_code, response.json()),
            (200, {"status": "subscribed", "email": "reader@example.com"}),
        )
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.SUBSCRIBED)
        self.assertIsNotNone(subscriber.confirmed_at)

    def test_subscribed_stays_subscribed(self):
        subscriber = make_subscriber()
        confirmed_at = subscriber.confirmed_at
        self.assertEqual(self.confirm(subscriber.token).json()["status"], "subscribed")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.confirmed_at, confirmed_at)

    def test_unsubscribed_is_not_resubscribed_by_an_old_link(self):
        subscriber = make_subscriber(status=Subscriber.UNSUBSCRIBED)
        response = self.confirm(subscriber.token)
        self.assertEqual(
            (response.status_code, response.json()),
            (200, {"status": "unsubscribed", "email": "reader@example.com"}),
        )
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.UNSUBSCRIBED)

    def test_unknown_or_missing_token_is_a_404(self):
        for token in ["nope", "", None]:
            response = self.confirm(token)
            self.assertEqual(
                (response.status_code, response.json()), (404, {"status": "invalid_token"})
            )
        self.assertEqual(self.post_json(CONFIRM, {}).status_code, 404)

    def test_only_post_is_allowed(self):
        self.assertEqual(self.client.get(CONFIRM).status_code, 405)


class UnsubscribeTests(NewsletterTestCase):
    def test_json_post_unsubscribes(self):
        subscriber = make_subscriber()
        response = self.post_json(UNSUBSCRIBE, {"token": subscriber.token})
        self.assertEqual(
            (response.status_code, response.json()),
            (200, {"status": "unsubscribed", "email": "reader@example.com"}),
        )
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.UNSUBSCRIBED)
        self.assertIsNotNone(subscriber.unsubscribed_at)

    def test_it_is_idempotent_and_works_for_pending_too(self):
        pending = make_subscriber(status=Subscriber.PENDING)
        for _ in range(2):
            self.assertEqual(
                self.post_json(UNSUBSCRIBE, {"token": pending.token}).json()["status"],
                "unsubscribed",
            )

    def test_form_post_redirects_with_303(self):
        subscriber = make_subscriber()
        response = self.client.post(UNSUBSCRIBE, {"token": subscriber.token})
        self.assertEqual(
            (response.status_code, response["Location"]),
            (303, "/newsletter/unsubscribe/?status=unsubscribed"),
        )
        response = self.client.post(UNSUBSCRIBE, {"token": "nope"})
        self.assertEqual(
            (response.status_code, response["Location"]),
            (303, "/newsletter/unsubscribe/?status=invalid_token"),
        )

    def test_one_click_post_gets_json_not_a_redirect(self):
        # What a mail client sends for the List-Unsubscribe-Post header (RFC 8058).
        subscriber = make_subscriber()
        response = self.client.post(
            f"{UNSUBSCRIBE}?token={subscriber.token}", {"List-Unsubscribe": "One-Click"}
        )
        self.assertEqual(
            (response.status_code, response.json()),
            (200, {"status": "unsubscribed", "email": "reader@example.com"}),
        )
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.UNSUBSCRIBED)

    def test_get_redirects_to_the_page_and_changes_nothing(self):
        subscriber = make_subscriber()
        response = self.client.get(f"{UNSUBSCRIBE}?token={subscriber.token}")
        self.assertEqual(
            (response.status_code, response["Location"]),
            (302, f"/newsletter/unsubscribe/?token={subscriber.token}"),
        )
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.SUBSCRIBED)
        self.assertEqual(self.client.get(UNSUBSCRIBE)["Location"], "/newsletter/unsubscribe/")

    def test_invalid_token_is_a_404_for_json_and_one_click(self):
        for response in [
            self.post_json(UNSUBSCRIBE, {"token": "nope"}),
            self.client.post(f"{UNSUBSCRIBE}?token=nope", {"List-Unsubscribe": "One-Click"}),
            self.post_json(UNSUBSCRIBE, {}),
        ]:
            self.assertEqual(
                (response.status_code, response.json()), (404, {"status": "invalid_token"})
            )

    def test_other_methods_are_405(self):
        self.assertEqual(self.client.put(UNSUBSCRIBE).status_code, 405)


class SubscriberModelTests(TestCase):
    def test_status_changes_set_the_timestamps(self):
        subscriber = Subscriber.objects.create(email=" Mixed@Example.com ")
        self.assertEqual(subscriber.email, "mixed@example.com")
        self.assertEqual((subscriber.confirmed_at, subscriber.unsubscribed_at), (None, None))
        subscriber.status = Subscriber.SUBSCRIBED  # As the admin form does.
        subscriber.save()
        self.assertIsNotNone(subscriber.confirmed_at)
        first = timezone.now()
        subscriber.unsubscribe()
        self.assertGreaterEqual(subscriber.unsubscribed_at, subscriber.confirmed_at)
        subscriber.status = Subscriber.PENDING
        subscriber.save()
        subscriber.unsubscribe()  # Every unsubscribe moves the timestamp.
        self.assertGreater(subscriber.unsubscribed_at, first)

    def test_tokens_are_unique_and_long(self):
        a, b = make_subscriber("a@example.com"), make_subscriber("b@example.com")
        self.assertNotEqual(a.token, b.token)
        self.assertGreaterEqual(len(a.token), 40)


class PostTestCase(NewsletterTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.post = make_post(
            "Hello World", datetime.date(2024, 5, 3), intro="An intro & more", published_hour=9
        )


@override_settings(FRONTEND_URL="https://example.org", DEFAULT_FROM_EMAIL="Blog <news@example.org>")
class EmailTests(PostTestCase):
    def test_confirmation_email(self):
        self.set_site_name("Prabuddh's Blog")
        subscriber = make_subscriber(status=Subscriber.PENDING)
        emails.send_confirmation(subscriber)
        [message] = mail.outbox
        self.assertEqual(message.subject, "Confirm your subscription to Prabuddh's Blog")
        self.assertEqual(message.from_email, "Blog <news@example.org>")
        url = f"https://example.org/newsletter/confirm/?token={subscriber.token}"
        self.assertIn(url, message.body)
        self.assertIn("you won't hear from us again", message.body)
        html = emails.html_of(message)
        self.assertIn(f'href="{url}"', html)
        self.assertIn("Confirm subscription", html)

    def set_site_name(self, name):
        settings_row = SiteSettings.for_site(Site.objects.get(is_default_site=True))
        settings_row.site_name = name
        settings_row.save()

    def test_site_name_comes_from_the_site_settings_or_the_default(self):
        self.set_site_name("Renamed")
        self.assertEqual(emails.site_name(), "Renamed")
        self.set_site_name("")
        self.assertEqual(emails.site_name(), "Prabuddh's Blog")

    @override_settings(NEWSLETTER_REPLY_TO="me@example.org")
    def test_post_email_has_text_and_html_absolute_links_and_headers(self):
        subscriber = make_subscriber()
        message = emails.build_issue(self.post, subscriber)
        self.assertEqual(message.subject, "Hello World")
        self.assertEqual(message.to, ["reader@example.com"])
        self.assertEqual(message.from_email, "Blog <news@example.org>")
        self.assertEqual(
            message.extra_headers["List-Unsubscribe"],
            f"<https://example.org/api/v2/newsletter/unsubscribe/?token={subscriber.token}>",
        )
        self.assertEqual(
            message.extra_headers["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click"
        )
        self.assertEqual(message.extra_headers["Reply-To"], "me@example.org")

        post_url = "https://example.org/2024/05/03/hello-world/"
        unsubscribe = f"https://example.org/newsletter/unsubscribe/?token={subscriber.token}"
        for part in (message.body, emails.html_of(message)):
            self.assertIn(post_url, part)
            self.assertIn(unsubscribe, part)
            self.assertIn("May 3, 2024", part)
            self.assertIn("min read", part)
        self.assertIn("An intro & more", message.body)
        self.assertIn("An intro &amp; more", emails.html_of(message))
        self.assertIn("subscribed at example.org", message.body)
        self.assertNotIn("<img", emails.html_of(message))
        self.assertNotIn('href="/', emails.html_of(message))

    def test_no_reply_to_header_unless_configured(self):
        message = emails.build_issue(self.post, make_subscriber())
        self.assertNotIn("Reply-To", message.extra_headers)

    def test_test_send_is_marked_and_has_a_dead_unsubscribe_link(self):
        message = emails.build_issue(self.post, to=["me@example.com"], test=True)
        self.assertEqual(message.subject, "[Test] Hello World")
        self.assertEqual(message.to, ["me@example.com"])
        self.assertIn("/newsletter/unsubscribe/?token=test", message.body)

    def test_featured_image_is_an_absolute_url_with_the_title_as_alt(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            image = Image.objects.create(title="A <nice> photo", file=get_test_image_file())
            self.post.featured_image = image
            self.post.save()
            html = emails.html_of(emails.build_issue(self.post, make_subscriber()))
        self.assertRegex(html, r'<img src="https://example\.org/media/images/[^"]+"')
        self.assertIn('alt="A &lt;nice&gt; photo"', html)
        self.assertIn("width:100%", html)

    def test_title_with_line_breaks_stays_one_header_line(self):
        self.post.title = "Two\nlines"
        self.assertEqual(emails.build_issue(self.post, make_subscriber()).subject, "Two lines")

    def test_message_ids_use_the_site_domain(self):
        subscriber = make_subscriber()
        for message in (
            emails.build_confirmation(subscriber),
            emails.build_issue(self.post, subscriber),
        ):
            self.assertRegex(message.message()["Message-ID"], r"^<[^@>]+@example\.org>$")


@override_settings(NEWSLETTER_SEND_DELAY=0)
class QueueTests(PostTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")

    def test_only_subscribed_people_get_deliveries(self):
        make_subscriber("a@example.com")
        make_subscriber("b@example.com")
        make_subscriber("pending@example.com", Subscriber.PENDING)
        make_subscriber("gone@example.com", Subscriber.UNSUBSCRIBED)
        issue = sending.queue_issue(self.post, self.user)
        self.assertEqual(issue.subject, "Hello World")
        self.assertEqual(issue.created_by, self.user)
        self.assertEqual(
            sorted(issue.deliveries.values_list("subscriber__email", flat=True)),
            ["a@example.com", "b@example.com"],
        )
        self.assertEqual(set(issue.deliveries.values_list("status", flat=True)), {"queued"})

    def test_refuses_a_post_that_is_not_live(self):
        Page.objects.filter(pk=self.post.pk).update(live=False)
        self.post.refresh_from_db()
        with self.assertRaisesMessage(sending.QueueError, "Publish the post first."):
            sending.queue_issue(self.post, self.user)
        self.assertEqual(Issue.objects.count(), 0)

    def test_refuses_a_post_that_was_already_emailed(self):
        make_subscriber()
        sending.queue_issue(self.post, self.user)
        with self.assertRaisesMessage(sending.QueueError, "already been emailed"):
            sending.queue_issue(self.post, self.user)
        self.assertEqual((Issue.objects.count(), Delivery.objects.count()), (1, 1))


@override_settings(NEWSLETTER_SEND_DELAY=0, FRONTEND_URL="https://example.org")
class SendDueTests(PostTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")

    def queue(self, *emails_):
        for email in emails_ or ["a@example.com"]:
            make_subscriber(email)
        return sending.queue_issue(self.post, self.user)

    def statuses(self):
        return dict(Delivery.objects.values_list("subscriber__email", "status"))

    def test_sends_and_marks_sent(self):
        self.queue("a@example.com", "b@example.com")
        self.assertEqual(sending.send_due(), 2)
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ["a@example.com", "b@example.com"])
        self.assertEqual(self.statuses(), {"a@example.com": "sent", "b@example.com": "sent"})
        self.assertFalse(Delivery.objects.filter(sent_at=None).exists())
        self.assertEqual(sending.send_due(), 0)  # Nothing is sent twice.
        self.assertEqual(len(mail.outbox), 2)

    def test_batch_size_limits_a_run(self):
        self.queue("a@example.com", "b@example.com", "c@example.com")
        self.assertEqual(sending.send_due(batch_size=2), 2)
        self.assertEqual(sending.send_due(batch_size=2), 1)

    def test_skips_people_who_unsubscribed_meanwhile(self):
        self.queue("a@example.com", "b@example.com")
        Subscriber.find("b@example.com").unsubscribe()
        self.assertEqual(sending.send_due(), 1)
        self.assertEqual(self.statuses(), {"a@example.com": "sent", "b@example.com": "skipped"})
        self.assertIn("no longer subscribed", Delivery.objects.get(status="skipped").last_error)

    def test_skips_when_the_post_is_no_longer_live(self):
        self.queue()
        Page.objects.filter(pk=self.post.pk).update(live=False)
        self.assertEqual(sending.send_due(), 0)
        delivery = Delivery.objects.get()
        self.assertEqual(delivery.status, "skipped")
        self.assertIn("no longer live", delivery.last_error)
        self.assertEqual(mail.outbox, [])

    def test_a_failure_is_retried_later_with_backoff(self):
        self.queue()
        with mock.patch(
            "django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("boom")
        ):
            self.assertEqual(sending.send_due(), 0)
        delivery = Delivery.objects.get()
        self.assertEqual((delivery.status, delivery.attempts), ("queued", 1))
        self.assertIn("OSError: boom", delivery.last_error)
        delay = delivery.next_attempt_at - timezone.now()
        self.assertTrue(datetime.timedelta(minutes=4) < delay <= datetime.timedelta(minutes=5))
        self.assertEqual(sending.send_due(), 0)  # Not due yet.

        for attempts, minutes in [(2, 10), (3, 20), (4, 40)]:
            Delivery.objects.update(next_attempt_at=timezone.now())
            with mock.patch(
                "django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("boom")
            ):
                sending.send_due()
            delivery.refresh_from_db()
            self.assertEqual((delivery.status, delivery.attempts), ("queued", attempts))
            delay = delivery.next_attempt_at - timezone.now()
            self.assertTrue(datetime.timedelta(minutes=minutes - 1) < delay)
            self.assertTrue(delay <= datetime.timedelta(minutes=minutes))

        # Due again and the server is back: it goes out.
        Delivery.objects.update(next_attempt_at=timezone.now())
        self.assertEqual(sending.send_due(), 1)
        self.assertEqual(Delivery.objects.get().status, "sent")

    def test_fails_for_good_after_five_attempts(self):
        self.queue()
        for _ in range(5):
            Delivery.objects.update(next_attempt_at=timezone.now())
            with mock.patch(
                "django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("boom")
            ):
                sending.send_due()
        delivery = Delivery.objects.get()
        self.assertEqual((delivery.status, delivery.attempts), ("failed", 5))
        Delivery.objects.update(next_attempt_at=timezone.now())
        self.assertEqual(sending.send_due(), 0)  # Failed rows aren't picked up again.

    def test_stops_after_three_failures_in_a_row_and_keeps_attempts_for_the_rest(self):
        self.queue(*[f"n{n}@example.com" for n in range(6)])
        with (
            mock.patch("django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("down")),
            self.assertLogs("newsletter.sending"),
        ):
            self.assertEqual(sending.send_due(), 0)
        tried = Delivery.objects.filter(attempts=1)
        self.assertEqual(tried.count(), 3)
        rest = Delivery.objects.filter(attempts=0)
        self.assertEqual(
            (rest.count(), set(rest.values_list("status", flat=True))), (3, {"queued"})
        )
        # The rest wait a while instead of being tried again straight away.
        self.assertEqual(sending.send_due(), 0)
        self.assertEqual(Delivery.objects.filter(attempts=0).count(), 3)

    def test_a_success_resets_the_count_of_failures_in_a_row(self):
        self.queue("a@example.com", "b@example.com", "c@example.com", "d@example.com")
        real_send = mail.EmailMultiAlternatives.send
        calls = []

        def flaky(message, *args, **kwargs):
            calls.append(message.to[0])
            if len(calls) in (1, 2, 4):
                raise OSError("flaky")
            return real_send(message, *args, **kwargs)

        with mock.patch("django.core.mail.EmailMultiAlternatives.send", flaky):
            self.assertEqual(sending.send_due(), 1)
        self.assertEqual(len(calls), 4)  # Never three failures in a row, so it went on.

    def test_stale_sending_rows_are_put_back_and_sent(self):
        self.queue()
        stale = timezone.now() - datetime.timedelta(minutes=16)
        Delivery.objects.update(status="sending", updated_at=stale)
        # Update() skips auto_now, so the row really looks stale.
        self.assertEqual(sending.send_due(), 1)
        self.assertEqual(Delivery.objects.get().status, "sent")

    def test_a_row_someone_else_is_sending_is_left_alone(self):
        self.queue()
        Delivery.objects.update(status="sending", updated_at=timezone.now())
        self.assertEqual(sending.send_due(), 0)
        self.assertEqual(mail.outbox, [])

    def test_the_claim_prevents_a_double_send(self):
        self.queue("a@example.com", "b@example.com")
        real_send = mail.EmailMultiAlternatives.send
        overlapping = []

        def send_while_another_run_starts(message, *args, **kwargs):
            if not overlapping:  # A second worker starts while the first is sending "a".
                overlapping.append(True)
                sending.send_due()
            return real_send(message, *args, **kwargs)

        with mock.patch(
            "django.core.mail.EmailMultiAlternatives.send", send_while_another_run_starts
        ):
            sending.send_due()
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ["a@example.com", "b@example.com"])
        self.assertEqual(set(self.statuses().values()), {"sent"})

    @override_settings(EMAIL_BACKEND="newsletter.tests.CountingBackend")
    def test_a_batch_shares_one_connection(self):
        CountingBackend.opened = 0
        self.queue("a@example.com", "b@example.com", "c@example.com")
        self.assertEqual(sending.send_due(), 3)
        self.assertEqual(CountingBackend.opened, 1)

    @override_settings(EMAIL_BACKEND="newsletter.tests.CountingBackend")
    def test_a_failed_send_reconnects_for_the_next_email(self):
        CountingBackend.opened = 0
        self.queue("a@example.com", "b@example.com")
        real_send = mail.EmailMultiAlternatives.send
        calls = []

        def drop_the_first(message, *args, **kwargs):
            calls.append(message.to[0])
            if len(calls) == 1:
                raise OSError("connection dropped")
            return real_send(message, *args, **kwargs)

        with (
            mock.patch("django.core.mail.EmailMultiAlternatives.send", drop_the_first),
            self.assertLogs("newsletter.sending"),
        ):
            self.assertEqual(sending.send_due(), 1)
        self.assertEqual(CountingBackend.opened, 2)
        self.assertEqual(self.statuses(), {calls[0]: "queued", calls[1]: "sent"})

    def test_retry_failed_requeues_failed_rows_only(self):
        issue = self.queue("a@example.com", "b@example.com")
        Delivery.objects.filter(subscriber__email="a@example.com").update(
            status="failed", attempts=5, last_error="x"
        )
        Delivery.objects.filter(subscriber__email="b@example.com").update(status="sent")
        self.assertEqual(sending.retry_failed(issue), 1)
        self.assertEqual(self.statuses(), {"a@example.com": "queued", "b@example.com": "sent"})
        self.assertEqual(Delivery.objects.get(status="queued").attempts, 0)
        self.assertEqual(sending.send_due(), 1)


@override_settings(NEWSLETTER_SEND_DELAY=0, FRONTEND_URL="https://example.org")
class WorkerTests(PostTestCase):
    def test_once_sends_everything_due_and_exits(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
        for n in range(3):
            make_subscriber(f"n{n}@example.com")
        sending.queue_issue(self.post, user)
        with self.assertLogs("newsletter.worker") as logs:
            call_command("newsletter_worker", "--once", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(Delivery.objects.filter(status="sent").count(), 3)
        self.assertTrue(any("3 sent, 0 failed" in line for line in logs.output))

    def test_once_with_an_empty_queue_exits(self):
        with self.assertLogs("newsletter.worker"):
            call_command("newsletter_worker", "--once", stdout=StringIO())

    def test_the_loop_survives_errors_and_sleeps_when_idle(self):
        sleeps = []

        def fake_sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) == 2:
                raise KeyboardInterrupt

        results = [RuntimeError("no such table"), BatchResult(sent=1), BatchResult()]
        with (
            mock.patch.object(newsletter_worker, "send_batch", side_effect=results),
            mock.patch.object(newsletter_worker.time, "sleep", fake_sleep),
            self.assertLogs("newsletter.worker") as logs,
        ):
            call_command("newsletter_worker", "--sleep", "7", stdout=StringIO())
        self.assertEqual(sleeps, [7.0, 7.0])  # After the error and after the empty batch.
        self.assertTrue(any("no such table" in line for line in logs.output))
        self.assertTrue(any("1 sent" in line for line in logs.output))


@override_settings(FRONTEND_URL="https://example.org", NEWSLETTER_SEND_DELAY=0)
class AdminTests(PostTestCase):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
        self.client.force_login(self.admin)
        self.url = f"/admin/newsletter/posts/{self.post.pk}/"

    def test_login_and_permission_are_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)  # To the admin login.

        editor = get_user_model().objects.create_user("editor", "e@example.com", "pw")
        editor.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.client.force_login(editor)
        response = self.client.get(self.url)
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)
        self.assertEqual(self.client.post(self.url, {"action": "send"}).status_code, 302)
        self.assertEqual(Issue.objects.count(), 0)

        editor.user_permissions.add(Permission.objects.get(codename="add_issue"))
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_only_blog_posts_have_the_page(self):
        home = HomePage.objects.get()
        self.assertEqual(self.client.get(f"/admin/newsletter/posts/{home.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/admin/newsletter/posts/99999/").status_code, 404)

    def test_page_before_sending(self):
        make_subscriber("a@example.com")
        make_subscriber("b@example.com")
        make_subscriber("c@example.com", Subscriber.PENDING)
        response = self.client.get(self.url)
        self.assertContains(response, "Send to 2 subscribers")
        self.assertContains(response, "Send a test")
        self.assertContains(response, 'value="admin@example.com"')
        # The email HTML sits escaped inside the iframe's srcdoc attribute.
        self.assertContains(response, 'srcdoc="\n&lt;!doctype html&gt;')
        self.assertContains(response, "https://example.org/2024/05/03/hello-world/")

    def test_page_for_a_post_that_is_not_live(self):
        make_subscriber()
        Page.objects.filter(pk=self.post.pk).update(live=False)
        response = self.client.get(self.url)
        self.assertContains(response, "Publish the post first")
        self.assertNotContains(response, "Send to 1 subscriber")

    def test_page_with_no_subscribers_has_no_send_button(self):
        response = self.client.get(self.url)
        self.assertContains(response, "No one is subscribed yet")
        self.assertNotContains(response, 'value="send"')

    def test_test_send(self):
        response = self.client.post(self.url, {"action": "test", "address": "me@example.com"})
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        [message] = mail.outbox
        self.assertEqual((message.to, message.subject), (["me@example.com"], "[Test] Hello World"))
        self.assertEqual(Issue.objects.count(), 0)
        self.assertContains(self.client.get(self.url), "A test email was sent to me@example.com.")

    def test_test_send_with_a_bad_address_or_a_mail_error_shows_a_message(self):
        self.client.post(self.url, {"action": "test", "address": "nope"})
        self.assertContains(self.client.get(self.url), "valid email address")
        with mock.patch(
            "django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("down")
        ):
            self.client.post(self.url, {"action": "test", "address": "me@example.com"})
        self.assertContains(self.client.get(self.url), "couldn&#x27;t be sent: OSError: down")
        self.assertEqual(mail.outbox, [])

    def test_send_queues_for_every_subscriber(self):
        make_subscriber("a@example.com")
        make_subscriber("b@example.com")
        response = self.client.post(self.url, {"action": "send"})
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        issue = Issue.objects.get()
        self.assertEqual((issue.post, issue.created_by), (self.post.page_ptr.specific, self.admin))
        self.assertEqual(issue.deliveries.count(), 2)
        self.assertEqual(mail.outbox, [])  # Only the worker sends.
        page = self.client.get(self.url)
        self.assertContains(page, "Queued for 2 subscribers.")
        self.assertNotContains(page, "Send to ")
        self.assertContains(page, "Queued: <strong>2</strong>")

    def test_sending_twice_is_refused(self):
        make_subscriber()
        self.client.post(self.url, {"action": "send"})
        self.client.post(self.url, {"action": "send"})
        self.assertEqual((Issue.objects.count(), Delivery.objects.count()), (1, 1))
        self.assertContains(self.client.get(self.url), "already been emailed")

    def test_page_after_sending_shows_errors_and_retry(self):
        make_subscriber()
        self.client.post(self.url, {"action": "send"})
        Delivery.objects.update(status="failed", attempts=5, last_error="OSError: refused")
        page = self.client.get(self.url)
        self.assertContains(page, "OSError: refused")
        self.assertContains(page, "Retry 1 failed")
        self.client.post(self.url, {"action": "retry"})
        delivery = Delivery.objects.get()
        self.assertEqual((delivery.status, delivery.attempts), ("queued", 0))
        self.assertNotContains(self.client.get(self.url), "Retry 1 failed")

    def test_menu_listings_render(self):
        make_subscriber("a@example.com")
        make_subscriber("b@example.com", Subscriber.PENDING)
        sending.queue_issue(self.post, self.admin)
        subscribers = self.client.get("/admin/newsletter/subscribers/")
        self.assertContains(subscribers, "a@example.com")
        self.assertContains(subscribers, "Waiting for confirmation")
        issues = self.client.get("/admin/newsletter/issues/")
        self.assertContains(issues, "Hello World")
        self.assertContains(issues, self.url)
        self.assertContains(issues, "0 / 1")
        self.assertContains(issues, "Sent posts")
        self.assertNotContains(issues, "Add sent post")
        self.assertEqual(self.client.get("/admin/newsletter/issues/new/").status_code, 404)
        self.assertContains(self.client.get("/admin/"), "Newsletter")

    def test_subscribers_export(self):
        make_subscriber("a@example.com")
        response = self.client.get("/admin/newsletter/subscribers/?export=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("a@example.com", b"".join(response.streaming_content).decode())

    def test_buttons_show_for_live_posts_only(self):
        parent_url = f"/admin/pages/{self.post.get_parent().pk}/"
        edit_url = f"/admin/pages/{self.post.pk}/edit/"
        self.assertContains(self.client.get(parent_url), self.url)
        self.assertContains(self.client.get(edit_url), self.url)
        self.assertContains(self.client.get(edit_url), "Email subscribers")

        sending.queue_issue(self.post, self.admin)
        self.assertContains(self.client.get(edit_url), "Newsletter status")

        draft = make_post("A Draft", datetime.date(2024, 6, 1))
        Page.objects.filter(pk=draft.pk).update(live=False)
        self.assertNotContains(
            self.client.get(f"/admin/pages/{draft.pk}/edit/"), f"/posts/{draft.pk}/"
        )
        self.assertNotContains(self.client.get(parent_url), f"/newsletter/posts/{draft.pk}/")
        # And not for other page types.
        home = HomePage.objects.get()
        self.assertNotContains(
            self.client.get(f"/admin/pages/{home.pk}/edit/"), "/newsletter/posts/"
        )


@override_settings(FRONTEND_URL="https://example.org")
class AfterPublishTests(PostTestCase):
    def publish_message(self, user):
        request = RequestFactory().post("/")
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        offer_to_email_post(request, self.post)
        return [str(m) for m in request._messages]

    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")

    def test_offers_to_email_the_post(self):
        make_subscriber("a@example.com")
        make_subscriber("b@example.com")
        [text] = self.publish_message(self.admin)
        self.assertIn("Email this post to 2 subscribers?", text)
        self.assertIn(f"/admin/newsletter/posts/{self.post.pk}/", text)

    def test_says_nothing_without_subscribers_or_when_already_sent_or_without_permission(self):
        self.assertEqual(self.publish_message(self.admin), [])
        make_subscriber()
        editor = get_user_model().objects.create_user("editor", "e@example.com", "pw")
        self.assertEqual(self.publish_message(editor), [])
        sending.queue_issue(self.post, self.admin)
        self.assertEqual(self.publish_message(self.admin), [])


class DeployCheckTests(TestCase):
    smtp = "django.core.mail.backends.smtp.EmailBackend"

    def warnings(self, **settings_):
        with override_settings(**settings_):
            return check_email_configured(None)

    def test_warns_when_smtp_is_still_the_default(self):
        [warning] = self.warnings(
            EMAIL_BACKEND=self.smtp,
            EMAIL_HOST="localhost",
            DEFAULT_FROM_EMAIL="webmaster@localhost",
        )
        self.assertIn("can't send", warning.msg)

    def test_warns_when_only_one_of_the_two_is_set(self):
        self.assertEqual(
            len(
                self.warnings(
                    EMAIL_BACKEND=self.smtp,
                    EMAIL_HOST="smtp.gmail.com",
                    DEFAULT_FROM_EMAIL="webmaster@localhost",
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                self.warnings(
                    EMAIL_BACKEND=self.smtp, EMAIL_HOST="localhost", DEFAULT_FROM_EMAIL="me@x.org"
                )
            ),
            1,
        )

    def test_quiet_when_configured_or_not_using_smtp(self):
        self.assertEqual(
            self.warnings(
                EMAIL_BACKEND=self.smtp, EMAIL_HOST="smtp.gmail.com", DEFAULT_FROM_EMAIL="me@x.org"
            ),
            [],
        )
        self.assertEqual(
            self.warnings(
                EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
                EMAIL_HOST="localhost",
                DEFAULT_FROM_EMAIL="webmaster@localhost",
            ),
            [],
        )

    def test_the_check_is_registered_for_deploy(self):
        from django.core.checks import registry

        self.assertIn(check_email_configured, registry.registry.deployment_checks)
