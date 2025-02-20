from arbiter3.portal.base import *

# For configuration details see:
# https://github.com/chpc-uofu/arbiter/blob/main/docs/settings.md

# ============================================================
#                          General
# ============================================================

# arbiter will ignore all accounts with a uid less than this number
ARBITER_MIN_UID = 1000

# arbiter will not set resource limits if enabled
ARBITER_PERMISSIVE_MODE = True

# ============================================================
#                         Prometheus
# ============================================================

# URL of your prometheus instance that scrapes the cgroup-wardens
PROMETHEUS_URL = 'https://your.prometheus.host:9090'

# arbiter will verify certificate of your prometheus instance if using tls if enabled
PROMETHEUS_VERIFY_SSL = True

# arbiter will use basic auth to communicate with your prometheus instance if set, e.g.
# PROMETHEUS_AUTH = ('username', 'password')
PROMETHEUS_AUTH = None

# ============================================================
#                        cgroup-warden
# ============================================================

# the name of the prometheus scrape job, needs to match the `job_name`
WARDEN_JOB = 'cgroup-warden'

# port the cgroup-wardens are listening on
WARDEN_PORT = 2112

# arbiter will verify the certificate of the cgroup-wardens if using tls if enabled
WARDEN_VERIFY_SSL = True

# arbiter will use tls (https) to communicate with the cgroup-wardens if enabled
WARDEN_USE_TLS = True

# arbiter will use bearer token auth to communicate with the cgroup-wardens if given, e.g.
# WARDEN_BEARER = 'super-secret-auth-token'
WARDEN_BEARER = None

# ============================================================
#                           Email
# ============================================================

ARBITER_NOTIFY_USERS = False  # turn on after email is configured

"""
import os

def user_lookup(username):
    realname = f'unknown real name'
    try:
        pwd_info = getpwnam(username)
        gecos = pwd_info.pw_gecos
        realname = gecos.rstrip() or realname
    except KeyError:
        pass
    
    email = f'{username}@localhost'

    return username, realname, email
"""

# user lookup function. Can be defined inline, like above example.
from arbiter3.arbiter.utils import default_user_lookup
ARBITER_USER_LOOKUP = default_user_lookup

# arbiter will send all violation emails to these addresses, e.g.
# ARBITER_ADMIN_EMAILS = ['bob@site.org', 'alice@site.org']
ARBITER_ADMIN_EMAILS = []

# arbiter will send mail from this address if set, e.g.
# ARBITER_FROM_EMAIL = 'arbiter@site.edu'
ARBITER_FROM_EMAIL = None

# arbiter will route the mail through this mail server
EMAIL_HOST = 'your.mail.server.edu'

# arbiter will communicate with the mail server through this port
EMAIL_PORT = 25

# arbiter will authenticate with the mail server with this username if set, e.g.
# EMAIL_HOST_USER = 'username'
EMAIL_HOST_USER = None

# arbiter will authenticate with the mail server with this password if set, e.g.
# EMAIL_HOST_PASSWORD = 'password'
EMAIL_HOST_PASSWORD = None

# ============================================================
#                          Django
# ============================================================
# django settings for running. To inherit default django settings, set variable
# to the same value, e.g.
#
# DEBUG = DEBUG 
#
# See https://docs.djangoproject.com/en/5.1/topics/settings/ for more information

DEBUG = True

# default DB is sqlite in this directory
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(__file__).resolve().parent / "db.sqlite3",
    }
}

SECRET_KEY = 'changeme'

ALLOWED_HOSTS = ['localhost']

TIME_ZONE = 'America/Denver'
