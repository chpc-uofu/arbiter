from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-wgoq*f367%a#m_^zsh=7g!@v+f(pu^ei2#y5gq_q(@y9k0qd^$"

DEBUG = True

ALLOWED_HOSTS = []

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

ROOT_URLCONF = "web_service.urls"

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

WSGI_APPLICATION = "web_service.wsgi.application"

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

import os

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
from prometheus_api_client import PrometheusConnect
url = os.environ["ARBITER_PROMETHEUS_HOST"]
user = os.environ.get("ARBITER_PROMETHEUS_USER")
password = os.environ.get("ARBITER_PROMETHEUS_PASS")
auth = (user, password) if user and password else None
disable_ssl = auth is None
PROMETHEUS_CONNECTION = PrometheusConnect(url=url, auth=auth, disable_ssl=disable_ssl)


# key used to authenticate with cgroup-agent 
ARBITER_CONTROL_KEY = os.environ.get("ARBITER_CONTROL_KEY")

# (optional) Default port for the warden service. Only required if your TSDB strips ports
ARBITER_WARDEN_PORT = os.environ.get("ARBITER_WARDEN_PORT", 2112)

ARBITER_WARDEN_PROTOCOL = os.environ.get("ARBITER_WARDEN_PROTOCOL", "https")
 

# domain used in default email lookup, and from email
ARBITER_EMAIL_DOMAIN = os.environ["ARBITER_EMAIL_DOMAIN"]

# arbiter sends mail via send_mail(), which requres these settings
EMAIL_HOST = os.environ["ARBITER_EMAIL_HOST"]
EMAIL_PORT = os.environ["ARBITER_EMAIL_PORT"]

# if your smtp server requires authentication
EMAIL_HOST_USER = os.environ.get("ARBITER_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("ARBITER_EMAIL_HOST_PASSWORD")

from typing import NamedTuple

class UserInfo(NamedTuple):
    username: str
    realname: str
    email: str

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from arbiter.models import Target

def ARBITER_USER_LOOKUP(target : "Target") -> UserInfo:
    """
    Looks up a user's information given the uid. 
    Information is used to send emails to users after a violation.
    """
    username = target.username
    realname = realname_lookup(username=username)
    email = email_lookup(username=username)
    return UserInfo(username, realname, email)

# your custom email lookup goes here.
def email_lookup(username : str) -> str:
    """
    Returns the email address of a user given the username.
    
    You can customize this function to suit your own needs,
    but it must take a username as an input and return the 
    desired email. 
    """

    return _default_email_lookup(username)

# your custom user lookup goes here. 
def realname_lookup(username: str) -> str:
    """
    Returns the realname of a user given the username.

    You can customize this function to suit your own needs,
    but it must take a uid as an input and return the
    desired username and realname.
    """

    return _default_realname_lookup(username=username)

def _default_email_lookup(username: str) -> str:
    """
    The default email address resolution method.
    """

    return f"{username}@{ARBITER_EMAIL_DOMAIN}"

from pwd import getpwnam

def _default_realname_lookup(username: str) -> str:
    """
    The default user info resolution method.
    """

    realname = f"unknown real name"
    try:
        pwd_info = getpwnam(username)
        gecos = pwd_info.pw_gecos
        realname = gecos.rstrip() or realname
    except KeyError:
        pass
    return realname