# Settings
The Arbiter Django app is configured with [Django Settings](https://docs.djangoproject.com/en/5.1/topics/settings/). Below describes the required settings for arbiter to run.

## General Django Settings

`DEBUG`: `bool`  
...

`ALLOWED_HOSTS`: `list[str]`
- A list of hostnames from which the Arbiter site can be accessed from.
- Should be set to the fully qualified domain name of the server running arbiter. 
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#allowed-hosts)

`SECRET_KEY`: `str`   
- A secret used for cryptographic signing and other security purposes.
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#secret-key)

`INSTALLED_APPS`: `list[str]` 
- Applications Django can use, Arbiter being one of them.
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#installed-apps)

`ROOT_URLCONF`: `str`  
...

`WSGI_APPLICATION`: `str`  
...

`LOGIN_REDIRECT_URL`: `str`  
...

`LOGOUT_REDIRECT_URL`: `str`  
...

`TIME_ZONE`: `str`  
...

`EMAIL_HOST`: `str`  
...

`EMAIL_PORT`: `str`  
...

`EMAIL_HOST_USER`: `str|None`  
... 

`EMAIL_HOST_PASSWORD`: `str|None`  
...

`LOGGING`: `dict`  
...

Example Settings:
```python
DEBUG = False
ALLOWED_HOSTS = ['your.arbiter.site.edu']
SECRET_KEY = 'your-super-secret-key'
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize", # new
    "arbiter", # new 
]

ROOT_URLCONF = "arbiter.urls" # match exactly
WSGI_APPLICATION = "arbiter.wsgi.application" # match exactly
LOGIN_REDIRECT_URL = "/" # match exactly
LOGOUT_REDIRECT_URL = "/" # match exactly

TIME_ZONE = "America/Denver"
EMAIL_HOST = "your.mail.server.site.edu"
EMAIL_PORT = "25"
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None
```

### Arbiter Specific Settings
`ARBITER_MIN_UID`: `int`  
...

`ARBITER_PERMISSIVE_MODE`: `bool`  
...

`ARBITER_USER_LOOKUP`: `str`  
...

`ARBITER_NOTIFY_USERS`: `bool`  
...

`ARBITER_EMAIL_DOMAIN`: `str`  
...

`PROMETHEUS_URL`: `str`  
...

`PROMETHEUS_VERIFY_SSL`: `bool`  
...

`PROMETHEUS_USER`: `str|None`  
...

`PROMETHEUS_PASS`: `str|None`  
...

`WARDEN_JOB`: `str`  
...

`WARDEN_PORT`: `int`  
...

`WARDEN_VERIFY_SSL`: `bool`  
...

`WARDEN_USE_TLS`: `bool`  
...

`WARDEN_BEARER`: `str|None`  
...

Example settings: 
```python
ARBITER_MIN_UID = 1000
ARBITER_PERMISSIVE_MODE = False
ARBITER_USER_LOOKUP = "arbiter.utils.default_user_lookup"
ARBITER_NOTIFY_USERS = True
ARBITER_EMAIL_DOMAIN = "test.site.edu"
PROMETHEUS_URL = "http://prometheus:9090"
PROMETHEUS_VERIFY_SSL = True
PROMETHEUS_USER = None
PROMETHEUS_PASS = None
WARDEN_JOB = "cgroup-warden"
WARDEN_PORT = 2112
WARDEN_VERIFY_SSL = False
WARDEN_USE_TLS = False
WARDEN_BEARER = "super-secret-bearer-token"
```