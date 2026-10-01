from .base import *  # noqa: F403
from .base import STORAGES, env

DEBUG = False

# Required: startup fails if any of these are missing.
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")
# base.py falls back to localhost for these; production must set them explicitly.
env("WAGTAILADMIN_BASE_URL")
env("FRONTEND_URL")

# Caddy terminates HTTPS and tells Django the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Caddy already redirects visitors from HTTP to HTTPS. Django's own redirect would also
# redirect the Nuxt server's internal http://backend:8000 requests, so it stays off.
SECURE_SSL_REDIRECT = False
SILENCED_SYSTEM_CHECKS = ["security.W008"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Start low; raise to a year (31536000) once HTTPS is confirmed working in production.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)

# Hashed, compressed static file names, so browsers never keep stale admin CSS/JS.
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
