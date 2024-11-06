import os
from portal.base import *
import tomllib

conf_file = os.getenv('ARBITER_CONF_FILE', os.path.join(BASE_DIR, 'config.toml'))

with open(conf_file, "rb") as f:
    config = tomllib.load(f)

    django = config.get('django', {})

    if debug := django.get('debug'):
        DEBUG = debug

    if secret_key := django.get('secret_key'):
        SECRET_KEY = secret_key

    if allowed_hosts := django.get('allowed_hosts'):
        ALLOWED_HOSTS = allowed_hosts

    if time_zone := django.get('time_zone'):
        TIME_ZONE = time_zone


    general = config.get('general', {})

    ARBITER_MIN_UID = general.get('min_uid', 1000)

    ARBITER_PERMISSIVE_MODE = general.get('permissive_mode', False)


    email = config['email']

    ARBITER_NOTIFY_USERS = email.get("notify_users", True)

    if ARBITER_NOTIFY_USERS:
        
        EMAIL_HOST = email['host']

        EMAIL_PORT = email['port']

        EMAIL_HOST_USER = email.get('user')

        EMAIL_HOST_PASSWORD = email.get('password')

        ARBITER_USER_LOOKUP = email.get('lookup_function')

        if not ARBITER_USER_LOOKUP:

            ARBITER_USER_LOOKUP = 'arbiter.utils.default_user_lookup'

            ARBITER_EMAIL_DOMAIN = email['domain']


    prometheus = config['prometheus']

    PROMETHEUS_URL = prometheus['url']

    PROMETHEUS_VERIFY_SSL = prometheus.get('verify_ssl', True)

    PROMETHEUS_USER = prometheus.get('user', None)

    PROMETHEUS_PASS = prometheus.get('password', None)


    warden = config['warden']

    WARDEN_JOB = warden.get('job', 'cgroup-warden')

    WARDEN_PORT = warden.get('port', '2112')

    WARDEN_VERIFY_SSL = warden.get('verify_ssl', True)

    WARDEN_USE_TLS = warden.get('use_tls', True)

    WARDEN_BEARER = warden.get('bearer', None)