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
schemas = ("http", "https")
ALLOWED_HOSTS = (environ.get("DJANGO_ALLOWED_HOSTS", "*"), "localhost", "127.0.0.1", "0.0.0.0")
logger.debug(f"{ALLOWED_HOSTS=}")
CSRF_TRUSTED_ORIGINS = [
    "{schema}://{address}:8080".format(schema=schema, address=address)
    for schema in schemas
    for address in ALLOWED_HOSTS
]
logger.debug(f"{CSRF_TRUSTED_ORIGINS=}")
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
    "imagekit",
    # APPS
    "gantt_chart",
]

if DEBUG:
    INSTALLED_APPS.append("django_extensions")
    SHELL_PLUS_PRINT_SQL_TRUNCATE = None

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
if environ.get("DATABASE_URL"):
    db_conf = parse(environ.get("DATABASE_URL"))
else:
    db_conf = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR.joinpath("db.sqlite3"),
    }
DATABASES = {"default": db_conf}


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
STATICFILES_DIRS = [BASE_DIR.joinpath("templates")]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.joinpath("media")


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
