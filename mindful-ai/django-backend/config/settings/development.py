
import logging

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING["root"]["level"] = "DEBUG"

LOGGING["loggers"]["apps"]["level"] = "DEBUG"
LOGGING["loggers"]["django"]["level"] = "DEBUG"

LOGGING["loggers"]["django.db.backends"]["level"] = "WARNING"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "10000/hour",
    "user": "100000/hour",
}

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

logging.debug("MindfulAI running with DEVELOPMENT settings.")
