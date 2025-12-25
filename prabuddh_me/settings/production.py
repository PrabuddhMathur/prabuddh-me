from .base import *
from decouple import config, Csv
import logging

# =====================================================
# ✅ General Production Settings
# =====================================================
DEBUG = False
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="prabuddh.in", cast=Csv())
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://prabuddh.in,https://www.prabuddh.in",
    cast=Csv(),
)

# =====================================================
# ✅ Security Settings
# =====================================================
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =====================================================
# ✅ Cookie / Session / CSRF Configuration
# =====================================================
SESSION_COOKIE_NAME = "__session"
SESSION_COOKIE_DOMAIN = ".prabuddh.in"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_USE_SESSIONS = True
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_DOMAIN = ".prabuddh.in"
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

USE_X_FORWARDED_HOST = True

# =====================================================
# ✅ Database (PostgreSQL via Docker Compose)
# =====================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432", cast=int),
        "CONN_MAX_AGE": 60,
    }
}

# =====================================================
# ✅ Caching
# =====================================================
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# =====================================================
# ✅ Wagtail
# =====================================================
WAGTAILADMIN_BASE_URL = config("WAGTAILADMIN_BASE_URL", default="https://prabuddh.in")

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# =====================================================
# ✅ Logging
# =====================================================
logging.basicConfig(level=logging.INFO)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose", "level": "INFO"}
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "wagtail": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
