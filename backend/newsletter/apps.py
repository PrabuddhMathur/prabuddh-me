from django.apps import AppConfig


class NewsletterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "newsletter"

    def ready(self):
        from . import checks  # noqa: F401  (registers the deploy check)
