from .base import *
from decouple import config, Csv
import os

# =====================================================
# ✅ General Local Settings
# =====================================================
DEBUG = config("DEBUG", default=True, cast=bool)
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-dev-key-change-in-production",
)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,*", cast=Csv())

# =====================================================
# ✅ Email & Debug Tools
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Optional: enable Django Debug Toolbar if installed
if config("USE_DEBUG_TOOLBAR", default=False, cast=bool):
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

# =====================================================
# ✅ Middleware
# =====================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

# =====================================================
# ✅ Static & Media Storage
# =====================================================
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# =====================================================
# ✅ Database
# =====================================================
USE_DOCKER_DB = config("USE_DOCKER_DB", default=False, cast=bool)

if USE_DOCKER_DB:
    # Using Docker Compose postgres
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="prabuddh_me_db"),
            "USER": config("DB_USER", default="prabuddh_me_db_user"),
            "PASSWORD": config("DB_PASSWORD", default="devpassword123"),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
        }
    }
else:
    # Local SQLite for quick development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

# =====================================================
# ✅ Logging
# =====================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
    },
}