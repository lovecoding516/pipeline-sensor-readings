"""Django settings for the pipeline readings viewer.

Deliberately a development-only configuration: the assignment asks for no
authentication and no deployment, so there is no secret management, no static
file pipeline and no production database here.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SAMPLE_CSV_PATH = Path(
    os.environ.get("SAMPLE_CSV_PATH", BASE_DIR.parent / "sensor_readings.csv")
)

# Tests build their own runs and assert on the empty state, so seeding is off
# by default under `manage.py test`.
LOAD_SAMPLE_ON_FIRST_REQUEST = os.environ.get(
    "LOAD_SAMPLE_ON_FIRST_REQUEST", "0" if "test" in sys.argv else "1"
) == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-a-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]"
).split(",")

# No auth, admin or sessions in this app, so contenttypes and friends are left
# out. staticfiles stays because it serves DRF's browsable API.
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "readings",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware has to precede CommonMiddleware so that CORS headers are
    # attached even to redirects CommonMiddleware generates.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "readings.middleware.SampleRunMiddleware",
]

# No sessions and no cookies, so there is no CSRF surface to protect and
# CsrfViewMiddleware is left out; DRF exempts APIView from it regardless.

ROOT_URLCONF = "pipeline.urls"
WSGI_APPLICATION = "pipeline.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# The Vite dev server.
CORS_ALLOWED_ORIGINS = os.environ.get(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "readings.exceptions.api_exception_handler",
}

# csv_import enforces the same ceiling on the decoded body.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
