"""WSGI config for the words project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "words.settings")

application = get_wsgi_application()
