from pathlib import Path
import os

# Do not use DEBUG = True if running in production
DEBUG: bool = True

# update with venv/bin python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY: str = "django-insecure-wgoq*f367%a#m_^zsh=7g!@v+f(pu^ei2#y5gq_q(@y9k0qd^$"

# update to the site you will host arbiter at
ALLOWED_HOSTS: list[str] = ["host.docker.internal", "localhost"]

# update to your time zone
TIME_ZONE: str = "America/Denver"

# update to your mail server
EMAIL_HOST: str = "mailhog"

# update to your mailserver port
EMAIL_PORT: str = "1025"

# update if your mailserver requires auth
EMAIL_HOST_USER: str | None = None

# update if your mailserver requires auth
EMAIL_HOST_PASSWORD: str | None = None

# arbiter will ignore uids below this number
ARBITER_MIN_UID: int = 1000

# arbiter will not set limits if enabled
ARBITER_PERMISSIVE_MODE: bool = False

# function arbiter uses to lookup users to email them
ARBITER_USER_LOOKUP: str = "arbiter.utils.default_user_lookup"

# arbiter will email users if enabled
ARBITER_NOTIFY_USERS: bool = True

# domain used by the default email resolution function, username@ARBITER_EMAIL_DOMAIN
ARBITER_EMAIL_DOMAIN: str = "test.site.edu"

# url for the prometheus instance holding cgroup-warden data
PROMETHEUS_URL: str = "http://prometheus:9090"

# arbiter will not verify certificate of prometheus if enabled
PROMETHEUS_VERIFY_SSL: bool = False

# update if your prometheus instance requires auth
PROMETHEUS_USER: str | None = None

# update if you prometheus instance requires auth
PROMETHEUS_PASS: str | None = None

# update if you have modified the scrape job name of the cgroup-wardens
WARDEN_JOB: str = "cgroup-warden"

# update if you have modified the port cgroup-warden runs on
WARDEN_PORT: int = 2112

# verify the ssl certificates of cgroup-warden 
WARDEN_VERIFY_SSL = False

# use https with cgroup warden
WARDEN_USE_TLS = True

# use bearer token authentication with cgroup warden
WARDEN_BEARER: str | None = "insecure-95axve4fn4j2u8ih0j1ltg272g1n297l8"

# Django configuration - modify only if you know what you are doing

BASE_DIR = Path(__file__).resolve().parent.parent

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

ROOT_URLCONF = "arbiter.urls"

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

WSGI_APPLICATION = "arbiter.wsgi.application"

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

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

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