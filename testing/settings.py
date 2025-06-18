from arbiter3.arbiter.utils import default_user_lookup
from arbiter3.portal.base import *

# For configuration details see:
# https://github.com/chpc-uofu/arbiter/blob/main/docs/settings.md

# ============================================================
#                          General
# ============================================================
ARBITER_MIN_UID = 1000

ARBITER_PERMISSIVE_MODE = False  # changeme to enable setting limits

ARBITER_LOG_LEVEL = 'debug'

# ============================================================
#                         Prometheus
# ============================================================

PROMETHEUS_URL = 'http://prometheus:9090'

PROMETHEUS_VERIFY_SSL = False

PROMETHEUS_USERNAME = None

PROMETHEUS_PASSWORD = None


# ============================================================
#                        cgroup-warden
# ============================================================
WARDEN_JOB = 'cgroup-warden'

WARDEN_PORT = 2112

WARDEN_VERIFY_SSL = False

WARDEN_USE_TLS = True

WARDEN_BEARER = 'insecure-95axve4fn4j2u8ih0j1ltg272g1n297l8'

WARDEN_RUNTIME = True


# ============================================================
#                           Email
# ============================================================

ARBITER_NOTIFY_USERS = True  # turn on after email is configured

ARBITER_USER_LOOKUP = default_user_lookup

ARBITER_ADMIN_EMAILS = []

ARBITER_FROM_EMAIL = 'arbiter@testing'

ARBITER_EMAIL_TEMPLATE_DIR = None

EMAIL_HOST = 'mailhog'  # changeme

EMAIL_PORT = 1025

EMAIL_HOST_USER = None

EMAIL_HOST_PASSWORD = None

# ============================================================
#                          Django
# ============================================================

DEBUG = True

WORKING_DIR = Path(__file__).resolve().parent.parent

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

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'host.docker.internal']

TIME_ZONE = 'America/Denver'

# ============================================================
#                          Django OIDC (optional)
# ============================================================
INSTALLED_APPS += [
    'mozilla_django_oidc',
]

AUTHENTICATION_BACKENDS = [
    'arbiter3.portal.oidc_backend.OIDCBackend',
    'django.contrib.auth.backends.ModelBackend',  # optional
]

LOGIN_URL = '/oidc/authenticate/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'http://keycloak:8080/realms/master/protocol/openid-connect/logout'

OIDC_RP_CLIENT_ID = 'test'
OIDC_RP_CLIENT_SECRET = 'DxBcevRlJlHYHUA7uZFkSsCqHvQ3D6Am'
OIDC_OP_AUTHORIZATION_ENDPOINT = 'http://keycloak:8080/realms/master/protocol/openid-connect/auth'
OIDC_OP_TOKEN_ENDPOINT = 'http://keycloak:8080/realms/master/protocol/openid-connect/token'
OIDC_OP_USER_ENDPOINT = 'http://keycloak:8080/realms/master/protocol/openid-connect/userinfo'
OIDC_CREATE_USER = True
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_OP_JWKS_ENDPOINT = 'http://keycloak:8080/realms/master/protocol/openid-connect/certs'
