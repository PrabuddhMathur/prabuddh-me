from .base import *
from decouple import config, Csv
import logging

# =====================================================
# ✅ General Production Settings
# =====================================================
DEBUG = False
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="blog.prabuddh.in,.prabuddh.in", cast=Csv())
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://blog.prabuddh.in,https://*.blog.prabuddh.in",
    cast=Csv(),
)

# =====================================================
# ✅ Security Settings (Cloudflare → Firebase → Cloud Run)
# =====================================================
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Disable HSTS temporarily (re-enable once fully stable)
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# =====================================================
# ✅ Cookie / Session / CSRF Configuration
# =====================================================
SESSION_COOKIE_NAME = "__session"
SESSION_COOKIE_DOMAIN = ".prabuddh.in"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "None"

CSRF_USE_SESSIONS = True  # store CSRF inside the session
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_DOMAIN = ".prabuddh.in"
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "None"

USE_X_FORWARDED_HOST = True

# =====================================================
# ✅ Database (PostgreSQL on VM with SSL)
# =====================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="443", cast=int),
        "OPTIONS": {
            "sslmode": "verify-full",
            "sslrootcert": os.getenv("DB_SSLROOTCERT"),  # /tmp/certs/ca.crt
            "sslcert": os.getenv("DB_SSLCERT"),          # /tmp/certs/client.crt
            "sslkey": os.getenv("DB_SSLKEY"),            # /tmp/certs/client.key
        },
        "CONN_MAX_AGE": 60,
    }
}

# =====================================================
# ✅ Storage (Google Cloud Storage)
# =====================================================
GS_BUCKET_NAME = config("GS_BUCKET_NAME")
GS_PROJECT_ID = config("GCP_PROJECT", default="prabuddh-me-5")

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "project_id": GS_PROJECT_ID,
            "file_overwrite": False,
            "querystring_auth": False,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "project_id": GS_PROJECT_ID,
            "location": "static",
            "file_overwrite": True,
            "querystring_auth": False,
        },
    },
}

# =====================================================
# ✅ Caching
# =====================================================
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# =====================================================
# ✅ Wagtail / App-Specific
# =====================================================
WAGTAILADMIN_BASE_URL = config("WAGTAILADMIN_BASE_URL", default="https://blog.prabuddh.in")

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
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

# =====================================================
# ✅ Optional Local Overrides
# =====================================================
try:
    from .local import *
except ImportError:
    pass
