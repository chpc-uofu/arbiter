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
            "level": os.getenv("ARBITER_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# prometheus configuration
url = os.environ["ARBITER_PROMETHEUS_HOST"]
user = os.environ.get("ARBITER_PROMETHEUS_USER")
password = os.environ.get("ARBITER_PROMETHEUS_PASS")
auth = (user, password) if user and password else None
disable_ssl = auth is None
PROMETHEUS_CONNECTION = PrometheusConnect(
    url=url, auth=auth, disable_ssl=disable_ssl)

# Name of your job used to cgroup instances of cgroup-warden. Used when determining
# where to apply limits.
WARDEN_SCRAPE_JOB_NAME = os.environ.get(
    "WARDEN_SCRAPE_JOB_NAME", "cgroup-warden")

# key used to authenticate with cgroup-agent
ARBITER_CONTROL_KEY = os.environ.get("ARBITER_CONTROL_KEY")

# (optional) Default port for the warden service. Only required if your TSDB strips ports
ARBITER_WARDEN_PORT = os.environ.get("ARBITER_WARDEN_PORT", 2113)

ARBITER_WARDEN_PROTOCOL = os.environ.get("ARBITER_WARDEN_PROTOCOL", "https")

# domain used in default email lookup, and from email
ARBITER_EMAIL_DOMAIN = os.environ["ARBITER_EMAIL_DOMAIN"]

# arbiter sends mail via send_mail(), which requres these settings
EMAIL_HOST = os.environ["ARBITER_EMAIL_HOST"]
EMAIL_PORT = os.environ["ARBITER_EMAIL_PORT"]

# if your smtp server requires authentication
EMAIL_HOST_USER = os.environ.get("ARBITER_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("ARBITER_EMAIL_HOST_PASSWORD")

USERINFO_MAPPER = "mycode.module.user_mapper"
