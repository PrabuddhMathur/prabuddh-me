"""A deploy-only check: warns when comments would work but nothing filters the spam."""

from django.conf import settings
from django.core.checks import Warning, register


@register(deploy=True)
def check_akismet_configured(app_configs, **kwargs):
    if settings.AKISMET_API_KEY:
        return []
    return [
        Warning(
            "Akismet isn't configured: comments go to the review queue without a spam check.",
            hint="Set AKISMET_API_KEY in backend/.env. See docs/comments.md.",
            id="comments.W001",
        )
    ]
