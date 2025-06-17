from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ImproperlyConfigured(Exception):
    pass


########## GENERAL SETTINGS ##########


try:
    ARBITER_MIN_UID = settings.ARBITER_MIN_UID
    assert isinstance(ARBITER_MIN_UID, int)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_MIN_UID is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_MIN_UID is an integer")


try:
    ARBITER_LOG_LEVEL = settings.ARBITER_LOG_LEVEL
    assert isinstance(ARBITER_LOG_LEVEL, str)
    match ARBITER_LOG_LEVEL:
        case 'debug':
            logging_level = logging.DEBUG
        case 'info':
            logging_level = logging.INFO
        case 'warning':
            logging_level = logging.WARNING
        case 'critical':
            logging_level = logging.CRITICAL
        case _:
            raise ValueError
    logging.getLogger().setLevel(logging_level)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_LOG_LEVEL is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_LOG_LEVEL is a string")
except ValueError:
    raise ImproperlyConfigured("setting ARBITER_LOG_LEVEL must be set to either 'debug', 'info', 'warning', or 'critical'")



########## EMAIL SETTINGS ##########

try:
    ARBITER_NOTIFY_USERS = settings.ARBITER_NOTIFY_USERS
    assert isinstance(ARBITER_NOTIFY_USERS, bool)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_NOTIFY_USERS is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_NOTIFY_USERS is a boolean")

try:
    ARBITER_USER_LOOKUP = settings.ARBITER_USER_LOOKUP
    assert callable(ARBITER_USER_LOOKUP)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_USER_LOOKUP is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_USER_LOOKUP is a callable")

try:
    EMAIL_HOST = settings.EMAIL_HOST
    if EMAIL_HOST is not None:
        assert isinstance(EMAIL_HOST, str)
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST is required")
except AssertionError:
    raise ImproperlyConfigured("setting EMAIL_HOST is a string or None")

try:
    EMAIL_PORT = settings.EMAIL_PORT
    if EMAIL_PORT is not None:
        assert isinstance(EMAIL_PORT, int)
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_PORT is required")
except AssertionError:
    raise ImproperlyConfigured("setting EMAIL_PORT is an integer or None")

try:
    EMAIL_HOST_USER = settings.EMAIL_HOST_PASSWORD
    if EMAIL_HOST_USER is not None:
        assert isinstance(EMAIL_HOST_USER, str)
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST_USER is required")
except AssertionError:
    raise ImproperlyConfigured("setting EMAIL_HOST_USER is a string or None")

try:
    EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
    if EMAIL_HOST_USER is not None:
        assert isinstance(EMAIL_HOST_PASSWORD, str)
except AttributeError:
    raise ImproperlyConfigured("setting EMAIL_HOST_PASSWORD is required")
except AssertionError:
    raise ImproperlyConfigured("setting EMAIL_HOST_PASSWORD is a string or None")

try:
    ARBITER_ADMIN_EMAILS = settings.ARBITER_ADMIN_EMAILS
    assert isinstance(ARBITER_ADMIN_EMAILS, list)
    for element in ARBITER_ADMIN_EMAILS:
        assert isinstance(element, str)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_ADMIN_EMAILS is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_ADMIN_EMAILS is a list of strings")

try: 
    ARBITER_FROM_EMAIL = settings.ARBITER_FROM_EMAIL
    if ARBITER_FROM_EMAIL is not None:
        assert isinstance(ARBITER_FROM_EMAIL, str)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_FROM_EMAIL is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_FROM_EMAIL is a string")

try: 
    ARBITER_EMAIL_TEMPLATE_DIR = settings.ARBITER_EMAIL_TEMPLATE_DIR
    if ARBITER_EMAIL_TEMPLATE_DIR is None:
        from arbiter3.arbiter.templates import arbiter
        ARBITER_EMAIL_TEMPLATE_DIR = arbiter.__path__
    else:
        assert isinstance(ARBITER_EMAIL_TEMPLATE_DIR, str)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_EMAIL_TEMPLATE_DIR is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_EMAIL_TEMPLATE_DIR is a string")


if ARBITER_ADMIN_EMAILS and EMAIL_HOST is None:
    raise ImproperlyConfigured("setting EMAIL_HOST is required if ARBITER_ADMIN_EMAILS is not empty")

if ARBITER_ADMIN_EMAILS and ARBITER_FROM_EMAIL is None:
    raise ImproperlyConfigured("setting ARBITER_FROM_EMAIL is required if ARBITER_ADMIN_EMAILS is not empty")

if ARBITER_NOTIFY_USERS and EMAIL_HOST is None:
    raise ImproperlyConfigured("setting EMAIL_HOST is required if ARBITER_NOTIFY_USERS=True")

if ARBITER_NOTIFY_USERS and ARBITER_FROM_EMAIL is None:
    raise ImproperlyConfigured("setting ARBITER_FROM_EMAIL is required if ARBITER_NOTIFY_USERS=True")


########## PROMETHEUS SETTINGS ##########

try:
    PROMETHEUS_URL = settings.PROMETHEUS_URL
    assert isinstance(PROMETHEUS_URL, str)
except AttributeError:
    raise ImproperlyConfigured("setting ARBITER_PROMETHEUS_URL is required")
except AssertionError:
    raise ImproperlyConfigured("setting ARBITER_PROMETHEUS_URL is a string")

try:
    PROMETHEUS_VERIFY_SSL = settings.PROMETHEUS_VERIFY_SSL
    assert isinstance(PROMETHEUS_VERIFY_SSL, bool)
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_VERIFY_SSL is required")
except AssertionError:
    raise ImproperlyConfigured("setting PROMETHEUS_VERIFY_SSL is a bool")

try:
    PROMETHEUS_USERNAME = settings.PROMETHEUS_USERNAME
    if PROMETHEUS_USERNAME is not None:
        assert isinstance(PROMETHEUS_USERNAME, str)
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_USERNAME is required")
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_USERNAME is a string or None")

try:
    PROMETHEUS_PASSWORD = settings.PROMETHEUS_PASSWORD
    if PROMETHEUS_PASSWORD is not None:
        assert isinstance(PROMETHEUS_PASSWORD, str)
except AttributeError:
    raise ImproperlyConfigured("setting PROMETHEUS_PASSWORD is required")
except AssertionError:
    raise ImproperlyConfigured("setting PROMETHEUS_PASSWORD is a string or None")

from arbiter3.arbiter.promclient import PrometheusSession
PROMETHEUS_CONNECTION = PrometheusSession(base_url=PROMETHEUS_URL, username=PROMETHEUS_USERNAME, password=PROMETHEUS_PASSWORD, verify=PROMETHEUS_VERIFY_SSL)

########## WARDEN SETTINGS ##########

try:
    WARDEN_JOB = settings.WARDEN_JOB
    assert isinstance(WARDEN_JOB, str)
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_JOB is required")
except AssertionError:
    raise ImproperlyConfigured("setting WARDEN_JOB is a string")

try:
    WARDEN_PORT = settings.WARDEN_PORT
    assert isinstance(WARDEN_PORT, int)
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_PORT is required")
except AssertionError:
    raise ImproperlyConfigured("setting WARDEN_PORT is an integer")

try:
    WARDEN_VERIFY_SSL = settings.WARDEN_VERIFY_SSL
    assert isinstance(WARDEN_VERIFY_SSL, bool)
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_VERIFY_SSL is required")
except AssertionError:
    raise ImproperlyConfigured("setting WARDEN_VERIFY_SSL is a bool")

try:
    WARDEN_USE_TLS = settings.WARDEN_USE_TLS
    assert isinstance(WARDEN_USE_TLS, bool)
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_DISABLE_TLS is required")
except AssertionError:
    raise ImproperlyConfigured("setting WARDEN_DISABLE_TLS is a bool")

try:
    WARDEN_BEARER = settings.WARDEN_BEARER
    if WARDEN_BEARER is not None:
        assert isinstance(WARDEN_BEARER, str)
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_BEARER is required")
except AssertionError:
    raise ImproperlyConfigured("setting WARDEN_BEARER is a string or None")

try:
    WARDEN_RUNTIME = settings.WARDEN_RUNTIME
    assert isinstance(WARDEN_RUNTIME, bool) 
except AttributeError:
    raise ImproperlyConfigured("setting WARDEN_RUNTIME is required")
except AssertionError:
    raise ImproperlyConfigured("setting WARDEN_RUNTIME is a bool")
