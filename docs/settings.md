# Settings
The arbiter settings are configured within the `settings.py` file generated with `arbiter-init`.
The settings are represented with native Python types.

## General
`ARBITER_MIN_UID` **(int)** : Arbiter will ignore all accounts with a uid less than this number.

`ARBITER_PERMISSIVE_MODE` **(bool)** : If enabled, Arbiter will not set 
resource limits.


## Prometheus
`PROMETHEUS_URL` **(string)** : URL of your prometheus instance that scrapes the wardens.

`PROMETHUS_VERIFY_SSL` **(bool)** : If enabled, arbiter will verify the certificate of your prometheus instance if using TLS.

`PROMETHEUS_AUTH` **(tuple[string, string] | None)** : If using basic auth, the username and password to query Prometheus with. 

## cgroup-warden
`WARDEN_JOB` **(string)** : The Prometheus scrape job name. Should be 'cgroup-warden'.

`WARDEN_PORT` **(int)** : The port the cgroup-warden is listening on.

`WARDEN_VERIFY_SSL` **(bool)** : If enabled, verify the certificate of the wardens if using TLS.

`WARDEN_USE_TLS` **(bool)** : If enabled, use TLS to make requests to the wardens (https).

`WARDEN_BEARER` **(string | None)** : If given, will be used as the bearer token to authenticate with the cgroup-wardens.

## Email
`ARBITER_NOTIFY_USERS` **(bool)** : If enabled, arbiter will email users about their violations.

`ARBITER_USER_LOOKUP` **(func)** : A function to lookup a users username, email, and realname given a username. This is a Python function.  

`ARBITER_ADMIN_EMAILS` **(list[string])** : A list of email addresses that arbiter will send all violations to. 

`ARBITER_FROM_EMAIL` **(string)** : The email address arbiter will send mail from.

`EMAIL_HOST` **(string)** : The mail server arbiter will route emails through. 

`EMAIL_PORT` **(int)** : The port arbiter will use with the mail server.

`EMAIL_HOST_USER` **(string)** If given, arbiter will use this username to authenticate with the mail server.

`EMAIL_HOST_PASSWORD` **(string)** If given, arbiter will use this password to authenticate with the mail server.

## Django

The following are Django specific settings. See [here](https://docs.djangoproject.com/en/5.1/topics/settings/) for details on all of the following.

`DEBUG` **(boolean)** : Whether to run the webserver in debug mode.

`DATABASES` **(dict)** : Database configuration.

`SECRET_KEY` **(string)** : A secret used for cryptographic signing and other security purposes.

`ALLOWED_HOSTS` **(list[string])** : A list of hostnames from which the Arbiter site can be accessed as.

`TIME_ZONE` **(string)** : Time zone used when displaying time.