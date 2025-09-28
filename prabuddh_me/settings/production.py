from .base import *
from decouple import config, Csv
import os

# Production settings
DEBUG = False

# In Cloud Run with Secret Manager, secrets are automatically injected as environment variables
# No need for custom parsing - just use config() directly

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Force HTTPS
USE_TLS = True

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
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

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
GS_PROJECT_ID = config('GCP_PROJECT')
GS_FILE_OVERWRITE = False
GS_DEFAULT_ACL = 'publicRead'

# Static and Media files on GCS
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "project_id": GS_PROJECT_ID,
            "file_overwrite": False,
            "default_acl": "publicRead",
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "project_id": GS_PROJECT_ID,
            "location": "static",
            "file_overwrite": True,
            "default_acl": "publicRead",
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

# Email configuration (using SendGrid or another service)
email_host = config('EMAIL_HOST', default='')
if email_host:
    EMAIL_HOST = email_host
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

# Wagtail settings for production
WAGTAILADMIN_BASE_URL = config('WAGTAILADMIN_BASE_URL', default='https://prabuddh.in')

# Performance optimizations
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Data upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

try:
    from .local import *
except ImportError:
    pass
