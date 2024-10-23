from prometheus_api_client import PrometheusConnect
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-wgoq*f367%a#m_^zsh=7g!@v+f(pu^ei2#y5gq_q(@y9k0qd^$"

DEBUG = True

ALLOWED_HOSTS = ["host.docker.internal", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "arbiter",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "server.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Denver"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

LOGIN_URL = "/arbiter/accounts/login/"
LOGIN_REDIRECT_URL = "/arbiter/"
LOGOUT_REDIRECT_URL = "/arbiter/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
        "arbiter": {
            "handlers": ["console"],
            "level": os.getenv("ARBITER_LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
    },
}

ARBITER_MIN_UID = 1000

ARBITER_PERMISSIVE_MODE = False

ARBITER_USER_LOOKUP = "arbiter.utils.default_user_lookup"

ARBITER_NOTIFY_USERS = True

ARBITER_EMAIL_DOMAIN = "test.site.edu"

EMAIL_HOST = "mailhog"

EMAIL_PORT = "1025"

EMAIL_DISABLE_AUTH = True

EMAIL_HOST_USER = None

EMAIL_HOST_PASSWORD = None

PROMETHEUS_URL = "http://prometheus:9090"

PROMETHEUS_DISABLE_AUTH = True

PROMETHEUS_DISABLE_SSL = True

PROMETHEUS_USER = None

PROMETHEUS_PASS = None

PROMETHUS_BEARER = None

WARDEN_JOB = "cgroup-warden"

WARDEN_PORT = 2112

WARDEN_DISABLE_SSL = False

WARDEN_DISABLE_AUTH = False

WARDEN_DISABLE_TLS = False

WARDEN_BEARER = "insecure-95axve4fn4j2u8ih0j1ltg272g1n297l8"
