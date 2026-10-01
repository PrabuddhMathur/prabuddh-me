from .base import *  # noqa: F403
from .base import env

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="django-insecure-local-development-only")

ALLOWED_HOSTS = ["*"]

# Print emails to the terminal unless a real SMTP server (Mailpit in Docker) is configured.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
