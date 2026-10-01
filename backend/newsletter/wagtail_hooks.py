"""
Newsletter in the Wagtail admin: a menu with the subscribers and the sent posts, the
"Email subscribers" page of a post, and buttons that lead to it.
"""

from django.contrib.auth.models import Permission
from django.db.models import Count, Q
from django.urls import include, path
from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.ui.tables import Column, DateColumn, TitleColumn
from wagtail.admin.viewsets import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets import Button
from wagtail.permission_policies import ModelPermissionPolicy

from blog.models import BlogPage

from . import admin_views
from .models import Delivery, Issue, Subscriber


class SubscriberViewSet(ModelViewSet):
    model = Subscriber
    name = "newsletter_subscribers"
    url_prefix = "newsletter/subscribers"
    icon = "group"
    menu_label = "Subscribers"
    add_to_reference_index = False
    form_fields = ["email", "status"]
    ordering = "-created_at"
    list_display = ["email", "status", "created_at", "confirmed_at"]
    list_filter = ["status"]
    search_fields = ["email"]
    search_backend_name = None  # Plain database search on the address.
    list_export = ["email", "status", "created_at", "confirmed_at", "unsubscribed_at"]
    export_filename = "newsletter-subscribers"
    copy_view_enabled = False


class SendersOnlyPolicy(ModelPermissionPolicy):
    """Read-only access to issues for everyone who may send a post. Nobody edits them."""

    def user_has_permission(self, user, action):
        return action == "view" and user.has_perm(admin_views.SEND_PERMISSION)

    def users_with_any_permission(self, actions):
        if "view" not in actions:
            return self.auth_model.objects.none()
        return super().users_with_any_permission(["add"])


class IssueViewSet(ModelViewSet):
    """A read-only list of the posts that were emailed, with the progress of each."""

    model = Issue
    name = "newsletter_issues"
    url_prefix = "newsletter/issues"
    icon = "doc-full"
    menu_label = "Sent posts"
    add_to_reference_index = False
    ordering = "-created_at"
    copy_view_enabled = False

    @property
    def permission_policy(self):
        return SendersOnlyPolicy(self.model)

    def get_permissions_to_register(self):
        # The one permission that matters is "add": it allows sending a post.
        return Permission.objects.filter(content_type__app_label="newsletter", codename="add_issue")

    def get_urlpatterns(self):
        # Only the listing and its results: no add, edit or delete views.
        return [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
        ]

    def get_index_view_kwargs(self, **kwargs):
        def count(status):
            return Count("deliveries", filter=Q(deliveries__status=status))

        queryset = Issue.objects.select_related("post").annotate(
            total=Count("deliveries"),
            sent=count(Delivery.SENT),
            failed=count(Delivery.FAILED),
            waiting=count(Delivery.QUEUED) + count(Delivery.SENDING),
        )
        columns = [
            TitleColumn(
                "subject",
                label="Post",
                get_url=lambda issue: admin_views.post_newsletter_url(issue.post),
                sort_key="subject",
            ),
            DateColumn("created_at", label="Queued", sort_key="created_at"),
            Column("sent", label="Sent", accessor=lambda i: f"{i.sent} / {i.total}"),
            Column("failed", label="Failed", accessor="failed"),
            Column("waiting", label="Waiting", accessor="waiting"),
        ]
        return super().get_index_view_kwargs(queryset=queryset, list_display=columns, **kwargs)


class NewsletterGroup(ViewSetGroup):
    menu_label = "Newsletter"
    menu_icon = "mail"
    menu_order = 400
    items = (SubscriberViewSet(), IssueViewSet())


@hooks.register("register_admin_viewset")
def register_newsletter_viewsets():
    return NewsletterGroup()


@hooks.register("register_admin_urls")
def register_newsletter_urls():
    patterns = [path("posts/<int:page_id>/", admin_views.post_newsletter, name="post")]
    return [path("newsletter/", include((patterns, "newsletter"), namespace="newsletter"))]


def _button(page, user, priority):
    """The "Email subscribers" button for a live blog post, for people who may send it."""
    if not (page.live and user.has_perm(admin_views.SEND_PERMISSION)):
        return None
    if page.specific_class is None or not issubclass(page.specific_class, BlogPage):
        return None
    label = (
        "Newsletter status"
        if Issue.objects.filter(post_id=page.pk).exists()
        else "Email subscribers"
    )
    return Button(label, admin_views.post_newsletter_url(page), icon_name="mail", priority=priority)


@hooks.register("register_page_listing_more_buttons")
def newsletter_listing_button(page, user, next_url=None):
    if button := _button(page, user, priority=45):
        yield button


@hooks.register("register_page_header_buttons")
def newsletter_header_button(page, user, view_name, next_url=None):
    if button := _button(page, user, priority=62):
        yield button


@hooks.register("after_publish_page")
def offer_to_email_post(request, page):
    """After publishing a post nobody has been emailed about, offer to do it."""
    if not isinstance(page, BlogPage) or not request.user.has_perm(admin_views.SEND_PERMISSION):
        return
    if Issue.objects.filter(post=page).exists():
        return
    count = admin_views.subscribed_count()
    if not count:
        return
    messages.info(
        request,
        f"Email this post to {count} subscriber{'s' if count != 1 else ''}?",
        buttons=[messages.button(admin_views.post_newsletter_url(page), "Email subscribers")],
    )
