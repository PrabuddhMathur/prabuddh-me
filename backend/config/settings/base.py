"""
Settings shared by every environment.

Anything that differs between environments is read from environment variables
(or backend/.env when it exists). See backend/.env.example for the full list.
"""

from pathlib import Path

import environ

PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_DIR.parent

env = environ.Env()
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(BASE_DIR / ".env")

DEBUG = False

# Public URL of this backend (admin, API). In production this is the same domain
# as the frontend, because Caddy routes /admin/, /api/ etc. here.
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL", default="http://localhost:8000")
WAGTAILAPI_BASE_URL = WAGTAILADMIN_BASE_URL

# Public URL of the Nuxt frontend. Used for previews and "View live" redirects.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")


# Email: confirmation emails (sent in the request) and newsletter posts (sent by the
# newsletter_worker command). Separate variables rather than EMAIL_URL, because an SMTP
# password containing "/" or "@" would need URL-encoding there.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=20)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# Optional Reply-To address on newsletter emails.
NEWSLETTER_REPLY_TO = env("NEWSLETTER_REPLY_TO", default="")
# Seconds the worker waits between two post emails (slow sending keeps providers happy).
NEWSLETTER_SEND_DELAY = env.float("NEWSLETTER_SEND_DELAY", default=1.0)
# Signup requests allowed per client IP per hour.
NEWSLETTER_SUBSCRIBE_LIMIT = env.int("NEWSLETTER_SUBSCRIBE_LIMIT", default=10)


# Application definition

INSTALLED_APPS = [
    "core",
    "blog",
    "home",
    "newsletter",
    "wagtail_headless_preview",
    "wagtail.api.v2",
    "wagtail.contrib.settings",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "rest_framework",
    "modelcluster",
    "taggit",
    "django_filters",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: SQLite, tuned for a web server.
# https://docs.djangoproject.com/en/5.2/ref/databases/#setting-pragma-options

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(env("SQLITE_PATH", default=str(BASE_DIR / "data" / "db.sqlite3"))),
        "OPTIONS": {
            # Take the write lock at the start of a transaction, so two writes at the
            # same moment wait for each other instead of failing with "database is locked".
            "transaction_mode": "IMMEDIATE",
            # Seconds to wait for that lock before giving up.
            "timeout": 20,
            # WAL lets readers carry on while a write is in progress.
            "init_command": (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA synchronous=NORMAL;"
                "PRAGMA temp_store=MEMORY;"
                "PRAGMA mmap_size=134217728;"
                "PRAGMA journal_size_limit=67108864;"
                "PRAGMA cache_size=2000;"
            ),
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (the Wagtail admin's CSS/JS, served by WhiteNoise) and uploaded media

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

# Uploaded images and documents. Overridable so tests and throwaway sites can use their own folder.
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))
MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Django allows 1000 fields per form by default; complex Wagtail page editors can exceed that.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000


# Wagtail

WAGTAIL_SITE_NAME = "Prabuddh's Blog"

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Allowed file extensions for documents in the document library.
WAGTAILDOCS_EXTENSIONS = ["csv", "docx", "key", "odt", "pdf", "pptx", "rtf", "txt", "xlsx", "zip"]
WAGTAILDOCS_MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB


# Headless previews: the admin's preview opens the Nuxt /preview page, which fetches
# the draft from /api/v2/page_preview/. "View live" redirects to the Nuxt page.
# https://github.com/torchbox/wagtail-headless-preview

WAGTAIL_HEADLESS_PREVIEW = {
    "CLIENT_URLS": {"default": f"{FRONTEND_URL}/preview"},
    "SERVE_BASE_URL": FRONTEND_URL,
    "REDIRECT_ON_PREVIEW": True,
}
