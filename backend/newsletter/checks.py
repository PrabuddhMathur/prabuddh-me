"""A deploy-only check: warns when the site would start but couldn't send any email."""

from django.conf import settings
from django.core.checks import Warning, register

SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


@register(deploy=True)
def check_email_configured(app_configs, **kwargs):
    if settings.EMAIL_BACKEND != SMTP_BACKEND:
        return []
    if settings.EMAIL_HOST != "localhost" and settings.DEFAULT_FROM_EMAIL != "webmaster@localhost":
        return []
    return [
        Warning(
            "Email isn't configured; the newsletter can't send.",
            hint=(
                "Set EMAIL_HOST (and EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) and "
                "DEFAULT_FROM_EMAIL in backend/.env. See docs/newsletter-production.md."
            ),
            id="newsletter.W001",
        )
    ]
