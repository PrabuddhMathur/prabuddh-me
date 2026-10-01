from .base import *  # noqa: F403
from .base import env

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="django-insecure-local-development-only")

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
