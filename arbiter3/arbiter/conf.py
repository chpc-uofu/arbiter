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
    ARBITER_NOTIFY_USERS = settings.ARBITER_NOTIFY_USERS
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_NOTIFY_USERS is required")

try:
    ARBITER_USER_LOOKUP = settings.ARBITER_USER_LOOKUP
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_USER_LOOKUP is required")

try:
    EMAIL_HOST = settings.EMAIL_HOST
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST is required")

try:
    EMAIL_HOST_USER = settings.EMAIL_HOST_PASSWORD
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST_USER is required")

try:
    EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST_PASSWORD is required")

try:
    ARBITER_ADMIN_EMAILS = settings.ARBITER_ADMIN_EMAILS
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_ADMIN_EMAILS is required")

try: 
    ARBITER_FROM_EMAIL = settings.ARBITER_FROM_EMAIL
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_FROM_EMAIL is required")


if ARBITER_NOTIFY_USERS and not EMAIL_HOST:
    raise ImproperlyConfigured("email.host is required if email.notify_users = true")

if ARBITER_NOTIFY_USERS and not ARBITER_USER_LOOKUP:
    raise ImproperlyConfigured("email.lookup_function is required if email.notify_users = true")


########## PROMETHEUS SETTINGS ##########

try:
    PROMETHEUS_URL = settings.PROMETHEUS_URL
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_PROMETHEUS_URL is required")

try:
    PROMETHEUS_VERIFY_SSL = settings.PROMETHEUS_VERIFY_SSL
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_VERIFY_SSL is required")

try:
    PROMETHEUS_USERNAME = settings.PROMETHEUS_USERNAME
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_USERNAME is required")

try:
    PROMETHEUS_PASSWORD = settings.PROMETHEUS_PASSWORD
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_PASSWORD is required")

########## WARDEN SETTINGS ##########

try:
    WARDEN_JOB = settings.WARDEN_JOB
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_JOB is required")

try:
    WARDEN_PORT = settings.WARDEN_PORT
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_PORT is required")

try:
    WARDEN_VERIFY_SSL = settings.WARDEN_VERIFY_SSL
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_VERIFY_SSL is required")

try:
    WARDEN_USE_TLS = settings.WARDEN_USE_TLS
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_DISABLE_TLS is required")

try:
    WARDEN_BEARER = settings.WARDEN_BEARER
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_BEARER is required")


from arbiter3.arbiter.promclient import PrometheusSession

PROMETHEUS_CONNECTION = PrometheusSession(base_url=PROMETHEUS_URL, username=PROMETHEUS_USERNAME, password=PROMETHEUS_PASSWORD, verify=PROMETHEUS_VERIFY_SSL)