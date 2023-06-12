from os import environ
from pathlib import Path

from dj_database_url import parse
from django.urls import reverse_lazy
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
SECRET_KEY = environ.get("DJANGO_SECRET_KEY", "super_secret_key")
DEBUG = True if environ.get("DJANGO_DEBUG") in ("1", "True", "true") else False  # noqa: SIM210
logger.debug(f"{DEBUG=}")
ALLOWED_HOSTS = (environ.get("DJANGO_ALLOWED_HOSTS", "*"), "localhost", "127.0.0.1")
logger.debug(f"{ALLOWED_HOSTS=}")
# LOGIN_URL = "/admin/login/"  # TODO
LOGIN_URL = reverse_lazy("login")  # TODO
LOGIN_REDIRECT_URL = reverse_lazy("index")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "django_filters",
    "rangefilter",
    "admin_auto_filters",
    "bootstrap_datepicker_plus",
    "django_select2",
    "django_extensions",  # TODO remove
    "imagekit",
    # APPS
    "gantt_chart",
]
SHELL_PLUS_PRINT_SQL_TRUNCATE = None  # TODO remove


# MIDDLEWARES
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# URLS
ROOT_URLCONF = "gantt.urls"


# TEMPLATES
TEMPLATES_DIR = BASE_DIR.joinpath("templates")
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
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


# WSGI
WSGI_APPLICATION = "gantt.wsgi.application"


# DATABASES
DATABASES = {
    "default": parse(environ.get("DATABASE_URL"))
    # {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": BASE_DIR / "db.sqlite3",
    # }
}


# PASSWORD VALIDATORS
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# DRF
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "SEARCH_PARAM": "term",
}


# Internationalization
LANGUAGE_CODE = "ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR.joinpath("static")
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.joinpath("media")


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
