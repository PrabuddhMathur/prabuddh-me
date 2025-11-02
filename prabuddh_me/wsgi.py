"""
WSGI config for prabuddh_me project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Default to production settings for security - override with DJANGO_SETTINGS_MODULE env var if needed
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prabuddh_me.settings.production")

application = get_wsgi_application()
