import os
import tomllib
import logging

from django.core.exceptions import ImproperlyConfigured

from portal.base import *


logger = logging.getLogger(__name__)

conf_file = os.getenv('ARBITER_CONF_FILE', os.path.join(BASE_DIR, 'config.toml'))

logger.info(f'reading config from {conf_file}')


with open(conf_file, "rb") as f:
    config = tomllib.load(f)

    django = config.get('django', {})

    DEBUG = django.get('debug') or DEBUG

    SECRET_KEY = django.get('secret_key') or SECRET_KEY

    ALLOWED_HOSTS = django.get('allowed_hosts') or ALLOWED_HOSTS

    TIME_ZONE = django.get('time_zone') or TIME_ZONE


    general = config.get('general', {})

    ARBITER_MIN_UID = general.get('min_uid', 1000)

    ARBITER_PERMISSIVE_MODE = general.get('permissive_mode', False)


    email = config.get('email', {})

    ARBITER_NOTIFY_USERS = email.get("notify_users", True)

    EMAIL_HOST = email.get('host')

    EMAIL_PORT = email.get('port', '25')

    EMAIL_HOST_USER = email.get('user')

    EMAIL_HOST_PASSWORD = email.get('password')

    ARBITER_USER_LOOKUP = email.get('lookup_function')

    ARBITER_ADMIN_EMAILS = email.get('admin_emails', [])

    if ARBITER_NOTIFY_USERS and not EMAIL_HOST:
        raise ImproperlyConfigured("email.host is required if email.notify_users = true")
    
    if ARBITER_NOTIFY_USERS and not ARBITER_USER_LOOKUP:
        raise ImproperlyConfigured("email.lookup_function is required if email.notify_users = true")

    ARBITER_FROM_EMAIL = email.get('from_email', None) 

    prometheus = config.get('prometheus', {})

    PROMETHEUS_URL = prometheus.get('url')

    PROMETHEUS_VERIFY_SSL = prometheus.get('verify_ssl', True)

    PROMETHEUS_USER = prometheus.get('user', None)

    PROMETHEUS_PASS = prometheus.get('password', None)
    
    if not PROMETHEUS_URL:
        raise ImproperlyConfigured('prometheus.url is required')
    
    warden = config.get('warden', {})

    WARDEN_JOB = warden.get('job', 'cgroup-warden')

    WARDEN_PORT = warden.get('port', '2112')

    WARDEN_VERIFY_SSL = warden.get('verify_ssl', True)

    WARDEN_USE_TLS = warden.get('use_tls', True)

    WARDEN_BEARER = warden.get('bearer', None)