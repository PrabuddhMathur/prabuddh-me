from .base import *
from decouple import config, Csv
import os

# Production settings
DEBUG = False

# In Cloud Run, secrets are injected as individual environment variables
# Just use config() directly - no need for custom parsing

# CSRF trusted origins - critical for admin login
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://blog.prabuddh.in,https://*.blog.prabuddh.in',
    cast=Csv()
)
# Security settings
# Disable SSL redirect since Cloudflare handles HTTPS
SECURE_SSL_REDIRECT = False
# Trust the X-Forwarded-Proto header from Cloudflare/Firebase/Cloud Run
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# Disable HSTS temporarily to avoid issues with multi-proxy setup
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False



# Cloud Run specific settings
if config('GAE_ENV', default=None) == 'standard' or config('CLOUD_RUN', default=False, cast=bool):
    # Running on Google Cloud Run
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Get the Cloud Run service URL
    ALLOWED_HOSTS = ['*']  # Cloud Run handles this
    
    # Trust the Cloud Run proxy for HTTPS headers
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Custom production deployment
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=['blog.prabuddh.in', '.prabuddh.in'], cast=Csv())

# Database configuration for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}

# Override SECRET_KEY with secret from Secret Manager
SECRET_KEY = config('SECRET_KEY')

# Google Cloud Storage configuration for production
GS_BUCKET_NAME = config('GS_BUCKET_NAME')
GS_PROJECT_ID = config('GCP_PROJECT', default='prabuddh-me-5')
GS_FILE_OVERWRITE = False
# Remove ACL settings for uniform bucket-level access
GS_DEFAULT_ACL = None
GS_OBJECT_PARAMETERS = {}
# Configure for public access without signed URLs
GS_QUERYSTRING_AUTH = False
# Skip file modification time checks for faster collectstatic
GS_EXPIRATION = None

SESSION_COOKIE_NAME = "__session"
CSRF_USE_SESSIONS = True

# Static and Media files on GCS
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

# Cache configuration (optional - can use Cloud Memorystore)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Logging configuration for Cloud Run
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'wagtail': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

SESSION_COOKIE_PATH = '/'
CSRF_COOKIE_PATH = '/'

# Email configuration (using SendGrid or another service)
email_host = config('EMAIL_HOST', default=None)
if email_host:
    EMAIL_HOST = email_host
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

# Wagtail settings for production
WAGTAILADMIN_BASE_URL = config('WAGTAILADMIN_BASE_URL', default='https://blog.prabuddh.in')

# Performance optimizations
# Cookie settings for multi-proxy setup (Cloudflare → Firebase → Cloud Run)
SESSION_COOKIE_SECURE = True  # HTTPS enforced
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Must be False for CSRF to work through proxies

# Critical: Use 'None' for SameSite to allow cookies through multiple proxies
SESSION_COOKIE_SAMESITE = 'None'  # Required for multi-proxy setups
CSRF_COOKIE_SAMESITE = 'None'  # Required for multi-proxy setups

CSRF_COOKIE_NAME = 'csrftoken'

SESSION_COOKIE_DOMAIN = ".prabuddh.in"
CSRF_COOKIE_DOMAIN = ".prabuddh.in"
# Allow forwarded host headers from proxies
USE_X_FORWARDED_HOST = True

# Data upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

try:
    from .local import *
except ImportError:
    pass
