"""
Comments in the Wagtail admin: a Comments menu with the list (waiting comments first),
approve / spam / like / reply from each row, the same in bulk, the reply page, and the
number of comments waiting for review in the menu and on the dashboard.

The comments are a snippet (that gives the list, filters, search, edit and delete views
and the bulk actions) with a few additions. Moderating happens only here: the public
site never knows who is logged in.
"""

from functools import cached_property, partial

from django.contrib.auth.models import Permission
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import redirect
from django.urls import path
from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, HelpPanel
from wagtail.admin.site_summary import SummaryItem
from wagtail.admin.ui.sidebar import LinkMenuItem
from wagtail.admin.ui.tables import Column, DateColumn, StatusTagColumn
from wagtail.admin.widgets import Button
from wagtail.admin.widgets.button import BaseButton
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.snippets.bulk_actions.delete import DeleteBulkAction
from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views import snippets

from . import admin_views, moderation
from .models import Comment

# Row buttons, in the order of the dropdown (lower first). Wagtail's own Edit is 10, Delete 30.
APPROVE, REPLY, LIKE, SPAM = 5, 15, 17, 25


class ActionButton(BaseButton):
    """A button that POSTs to its URL, for actions that change something."""

    template_name = "comments/admin/action_button.html"

    def __init__(self, label, url, *, in_row=False, **kwargs):
        # In the row itself, as a button, or in the "More" dropdown.
        if in_row:
            kwargs["classname"] = "button button-small button-secondary"
        super().__init__(label=label, url=url, **kwargs)
        self.allow_in_dropdown = not in_row


class CommentPermissionPolicy(ModelPermissionPolicy):
    """Comments come from readers, and replies from the reply page: nobody adds one by hand."""

    def user_has_permission(self, user, action):
        return action != "add" and super().user_has_permission(user, action)

    def users_with_any_permission(self, actions):
        actions = [action for action in actions if action != "add"]
        if not actions:
            return self.auth_model.objects.none()
        return super().users_with_any_permission(actions)


class CommentIndexView(snippets.IndexView):
    def get_list_more_buttons(self, instance):
        buttons = super().get_list_more_buttons(instance)
        if not self.request.user.has_perm(admin_views.CHANGE_PERMISSION):
            return buttons

        def action(name, label, icon, priority, in_row=False):
            url = admin_views.action_url(instance, name)
            return ActionButton(label, url, icon_name=icon, priority=priority, in_row=in_row)

        # A comment waiting for review gets its two decisions as buttons in its row.
        pending = instance.status == Comment.PENDING
        if instance.status != Comment.APPROVED:
            buttons.append(action("approve", "Approve", "check", APPROVE, in_row=pending))
        if instance.status != Comment.SPAM:
            buttons.append(action("spam", "Mark as spam", "warning", SPAM, in_row=pending))
            reply_url = admin_views.reply_url(instance)
            buttons.append(Button("Reply", reply_url, icon_name="comment", priority=REPLY))
        if instance.status == Comment.APPROVED:
            if instance.liked:
                buttons.append(action("unlike", "Remove your like", "cross", LIKE))
            else:
                buttons.append(action("like", "Like", "tick", LIKE))
        return buttons


class CommentDeleteView(snippets.DeleteView):
    @property
    def confirmation_message(self):
        message = super().confirmation_message
        if self.object.replies.exists():
            message += " The replies to it are deleted too."
        return message


class CommentsMenuItem(MenuItem):
    """The menu entry, with the number of comments waiting for review."""

    def is_shown(self, request):
        user = request.user
        return user.has_perm(admin_views.CHANGE_PERMISSION) or user.has_perm(
            admin_views.DELETE_PERMISSION
        )

    def render_component(self, request):
        label = self.label
        if count := admin_views.pending_count():
            label = f"{label} ({count})"
        return LinkMenuItem(
            self.name,
            label,
            self.url,
            icon_name=self.icon_name,
            classname=self.classname,
            attrs=self.attrs,
        )


class CommentViewSet(snippets.SnippetViewSet):
    model = Comment
    icon = "comment"
    menu_label = "Comments"
    menu_name = "comments"
    menu_order = 420
    add_to_admin_menu = True
    add_to_reference_index = False
    url_prefix = "comments"
    url_namespace = admin_views.NAMESPACE

    menu_item_class = CommentsMenuItem
    index_view_class = CommentIndexView
    delete_view_class = CommentDeleteView
    copy_view_enabled = False

    # Waiting comments first, then the newest.
    ordering = ["review_order", "-created_at"]
    list_per_page = 25
    list_display = [
        "excerpt",
        "name",
        "email",
        Column("post", label="Post", accessor="post.title", sort_key="post__title"),
        StatusTagColumn(
            "get_status_display",
            label="Status",
            sort_key="status",
            primary=lambda comment: comment.status == Comment.APPROVED,
        ),
        Column(
            "spam_check", label="Akismet", accessor="get_spam_check_display", sort_key="spam_check"
        ),
        Column(
            "liked",
            label="Liked",
            accessor=lambda comment: "✓" if comment.liked else "",
            sort_key="liked",
        ),
        DateColumn("created_at", label="Posted", sort_key="created_at"),
    ]
    list_filter = ["status", "spam_check", "post"]
    search_fields = ["name", "email", "body"]
    search_backend_name = None  # Plain database search.

    # What a reader wrote is edited only to remove something; the status never, because it
    # has to change through the actions, which tell Akismet and send the emails.
    panels = [
        HelpPanel(template="comments/admin/details_panel.html", heading="Details"),
        FieldPanel("name"),
        FieldPanel("body"),
        FieldPanel("liked"),
    ]

    @property
    def permission_policy(self):
        return CommentPermissionPolicy(self.model)

    def get_permissions_to_register(self):
        # "Add" has no use here, and nothing needs "view".
        return Permission.objects.filter(
            content_type__app_label="comments", codename__in=["change_comment", "delete_comment"]
        )

    def get_queryset(self, request):
        return Comment.objects.select_related("post").annotate(
            review_order=Case(
                When(status=Comment.PENDING, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )

    def get_urlpatterns(self):
        patterns = super().get_urlpatterns()
        patterns.append(path("<int:pk>/reply/", admin_views.reply, name="reply"))
        for action in ("approve", "spam", "like", "unlike"):
            patterns.append(
                path(f"<int:pk>/{action}/", partial(admin_views.act, action=action), name=action)
            )
        return patterns


register_snippet(CommentViewSet)


# Bulk actions


class ListingBulkActionMixin:
    """
    "Select all in listing" has to mean the comments the list is showing, with its filters
    and search, which is what the link says. Wagtail's default for snippets is every comment:
    selecting all of the waiting comments and marking them as spam would hit them all.
    """

    def get_all_objects_in_listing_query(self, parent_id):
        index = Comment.snippet_viewset.index_view
        view = index.view_class(**index.view_initkwargs)
        view.setup(self.request)
        return view.get_queryset().values_list("pk", flat=True)


class CommentBulkAction(ListingBulkActionMixin, SnippetBulkAction):
    """Runs one of the moderation actions on the selected comments, after a confirmation."""

    models = [Comment]
    template_name = "comments/admin/confirm_bulk_action.html"
    classes = set()
    action = ""  # The name moderation.run() knows.
    verb = ""
    confirm_button = ""
    button_class = ""
    note = ""

    def check_perm(self, comment):
        return self.request.user.has_perm(admin_views.CHANGE_PERMISSION)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            verb=self.verb,
            confirm_button=self.confirm_button,
            button_class=self.button_class,
            note=self.note,
            **kwargs,
        )

    def form_valid(self, form):
        # Wagtail runs a bulk action inside one database transaction. These also tell Akismet
        # and send emails, which can take seconds, and SQLite would stay locked for writing
        # all that time. So they run without it: each comment is saved on its own. (This
        # skips Wagtail's before/after bulk action hooks, which nothing here uses.)
        objects, _ = self.get_actionable_objects()
        outcome = moderation.run(self.action, objects)
        if outcome.changed:
            messages.success(self.request, admin_views.done_message(self.action, outcome.changed))
        else:
            messages.warning(self.request, admin_views.NOTHING_TO_DO[self.action])
        admin_views.show_warnings(self.request, outcome.warnings)
        return redirect(self.next_url)


class ApproveBulkAction(CommentBulkAction):
    display_name = "Approve"
    action_type = "approve"
    action = "approve"
    aria_label = "Approve selected comments"
    action_priority = 10
    verb = "Approve"
    confirm_button = "Yes, approve"
    note = "Whoever asked for an email when someone replies gets the message that confirms it."


class SpamBulkAction(CommentBulkAction):
    display_name = "Mark as spam"
    action_type = "spam"
    action = "spam"
    aria_label = "Mark selected comments as spam"
    action_priority = 20
    classes = {"serious"}
    verb = "Mark as spam"
    confirm_button = "Yes, mark as spam"
    button_class = "serious"
    note = "They are hidden, and Akismet (when it is on) learns from it."


class DeleteCommentsBulkAction(ListingBulkActionMixin, DeleteBulkAction):
    """The snippets' delete, for comments only, that says the replies go too."""

    models = [Comment]
    template_name = "comments/admin/confirm_bulk_delete.html"


hooks.register("register_bulk_action", ApproveBulkAction)
hooks.register("register_bulk_action", SpamBulkAction)
# Later than the snippets' own delete, so that this one is used for comments.
hooks.register("register_bulk_action", DeleteCommentsBulkAction, order=100)


# Dashboard


class PendingCommentsSummaryItem(SummaryItem):
    """The number of comments waiting for review, next to the page and image counts."""

    order = 150
    template_name = "comments/admin/summary_pending.html"

    def is_shown(self):
        return self.request.user.has_perm(admin_views.CHANGE_PERMISSION) and self.count > 0

    @cached_property
    def count(self):
        return admin_views.pending_count()

    def get_context_data(self, parent_context):
        return {"count": self.count, "url": admin_views.index_url(status=Comment.PENDING)}


@hooks.register("construct_homepage_summary_items")
def add_pending_comments(request, items):
    items.append(PendingCommentsSummaryItem(request))
