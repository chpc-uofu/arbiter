from arbiter3.arbiter.utils import default_user_lookup
from arbiter3.portal.base import *

# For configuration details see:
# https://github.com/chpc-uofu/arbiter/blob/main/docs/settings.md

# ============================================================
#                          General
# ============================================================
ARBITER_MIN_UID = 1000

ARBITER_PERMISSIVE_MODE = True  # changeme to enable setting limits

# ============================================================
#                         Prometheus
# ============================================================

PROMETHEUS_URL = 'https://your.prometheus.host:9090'

PROMETHEUS_VERIFY_SSL = True

# if using basic auth set to tuple (username, password)
PROMETHEUS_AUTH = None


# ============================================================
#                        cgroup-warden
# ============================================================
WARDEN_JOB = 'cgroup-warden'

WARDEN_PORT = 2112

WARDEN_VERIFY_SSL = True

WARDEN_USE_TLS = True

WARDEN_BEARER = None


# ============================================================
#                           Email
# ============================================================

ARBITER_NOTIFY_USERS = False  # turn on after email is configured


ARBITER_USER_LOOKUP = default_user_lookup

ARBITER_ADMIN_EMAILS = []

ARBITER_FROM_EMAIL = None

EMAIL_HOST = 'your.mail.server.edu'  # changeme

EMAIL_PORT = 25

EMAIL_HOST_USER = None

EMAIL_HOST_PASSWORD = None

# ============================================================
#                          Django
# ============================================================

DEBUG = True

WORKING_DIR = Path(__file__).resolve().parent

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": WORKING_DIR / "db.sqlite3",
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'changeme'

ALLOWED_HOSTS = ALLOWED_HOSTS

TIME_ZONE = TIME_ZONE
