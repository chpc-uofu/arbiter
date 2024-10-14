from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


########## GENERAL SETTINGS ##########


try:
    ARBITER_MIN_UID = settings.ARBITER_MIN_UID
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_MIN_UID is required")

try:
    ARBITER_PERMISSIVE_MODE = settings.ARBITER_PERMISSIVE_MODE
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_PERMISSIVE_MODE is required")


########## EMAIL SETTINGS ##########


try:
    ARBITER_USER_LOOKUP = settings.ARBITER_USER_LOOKUP
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_USER_LOOKUP is required")

try:
    ARBITER_NOTIFY_USERS = settings.ARBITER_NOTIFY_USERS
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_NOTIFY_USERS is required")

try:
    ARBITER_EMAIL_DOMAIN = settings.ARBITER_EMAIL_DOMAIN
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_EMAIL_DOMAIN is required")

try:
    EMAIL_HOST = settings.EMAIL_HOST
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST is required")

try:
    EMAIL_DISABLE_AUTH = ImproperlyConfigured(
        "setting EMAIL_DISABLE_AUTH is required"
    )
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_DISABLE_AUTH is required")

try:
    EMAIL_HOST_USER = settings.EMAIL_HOST_PASSWORD
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST_USER is required")

try:
    EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST_PASSWORD is required")


########## PROMETHEUS SETTINGS ##########


try:
    PROMETHEUS_URL = settings.PROMETHEUS_URL
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_PROMETHEUS_URL is required")

try:
    PROMETHEUS_DISABLE_SSL = settings.PROMETHEUS_DISABLE_SSL
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_DISABLE_SSL is required")

try:
    PROMETHEUS_DISABLE_AUTH = settings.PROMETHEUS_DISABLE_AUTH
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_DISABLE_AUTH is required")

try:
    PROMETHEUS_USER = settings.PROMETHEUS_USER
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_USER is required")

try:
    PROMETHEUS_PASS = settings.PROMETHEUS_PASS
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_PASS is required")


########## WARDEN SETTINGS ##########

try:
    WARDEN_JOB = settings.WARDEN_JOB
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_JOB is required")

try:
    WARDEN_PORT = settings.WARDEN_PORT
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_JOB_PORT is required")

try:
    WARDEN_DISABLE_SSL = settings.WARDEN_DISABLE_SSL
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_DISABLE_SSL is required")

try:
    WARDEN_DISABLE_TLS = settings.WARDEN_DISABLE_TLS
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_DISABLE_TLS is required")

try:
    WARDEN_DISABLE_AUTH = settings.WARDEN_DISABLE_AUTH
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_DISABLE_AUTH is required")

try:
    WARDEN_BEARER = settings.WARDEN_BEARER
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_BEARER is required")

from prometheus_api_client import PrometheusConnect

if not PROMETHEUS_DISABLE_AUTH:
    auth = (PROMETHEUS_USER, PROMETHEUS_PASS)
else:
    auth = None

PROMETHEUS_CONNECTION = PrometheusConnect(
    url=PROMETHEUS_URL, auth=auth, disable_ssl=PROMETHEUS_DISABLE_SSL
)

if not PROMETHEUS_CONNECTION.check_prometheus_connection():
    raise ImproperlyConfigured(
        "Prometheus cannot be reached. Is PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASS, and PROMETHEUS_DISABLE_SSL properly configured?"
    )
