
import logging

from .base import *

DEBUG = False

SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 31_536_000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

CACHES["default"]["TIMEOUT"] = 600

LOGGING["root"]["level"] = "WARNING"

LOGGING["loggers"]["apps"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "WARNING"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

DATABASES["default"]["CONN_MAX_AGE"] = 300

logging.info("MindfulAI running with PRODUCTION settings.")
