from .base import *
from decouple import config, Csv

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default="django-insecure-ge&!nl%%ub%bujv(!4$2dey6u7@qdhovcp*f1hev3(h*z+ej%j")

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,*', cast=Csv())

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development-specific middleware (add debug toolbar if needed)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Add whitenoise for static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

# Static files configuration for development
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# For local development, use local file storage if GCS is not configured
if not config('GS_BUCKET_NAME', default=None):
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Database for development (can use Cloud SQL Proxy or local PostgreSQL)
if config('USE_CLOUD_SQL_PROXY', default=False, cast=bool):
    # Using Cloud SQL Proxy for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': '127.0.0.1',  # Cloud SQL Proxy runs locally
            'PORT': '5432',
        }
    }

# Logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

try:
    from .local import *
except ImportError:
    pass
