from .base import *
from decouple import config, Csv
import os

# =====================================================
# ✅ General Local Settings
# =====================================================
DEBUG = config("DEBUG", default=True, cast=bool)
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-ge&!nl%%ub%bujv(!4$2dey6u7@qdhovcp*f1hev3(h*z+ej%j",
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
# Force local filesystem for development
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# =====================================================
# ✅ Database
# =====================================================
USE_CLOUD_SQL_PROXY = config("USE_CLOUD_SQL_PROXY", default=False, cast=bool)

if USE_CLOUD_SQL_PROXY:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": "127.0.0.1",  # Cloud SQL Proxy runs locally
            "PORT": "5432",
        }
    }
else:
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

# =====================================================
# ✅ Optional Local Overrides
# =====================================================
try:
    from .local import *
except ImportError:
    pass
