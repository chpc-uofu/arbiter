# Settings
The arbiter settings are configured within the `settings.py` file generated with `arbiter-init`.
The settings are represented with native Python types.

## General
`ARBITER_MIN_UID` **(int)** : Arbiter will ignore all accounts with a uid less than this number.

`ARBITER_PERMISSIVE_MODE` **(bool)** : If enabled, Arbiter will not set 
resource limits.

`ARBITER_LOG_LEVEL` **(string)** : The level of messages to log out. Options are `debug`, `info`, `warning`, and `critical`. 

## Prometheus
`PROMETHEUS_URL` **(string)** : URL of your prometheus instance that scrapes the wardens.

`PROMETHEUS_VERIFY_SSL` **(bool)** : If enabled, arbiter will verify the certificate of your prometheus instance if using TLS.

`PROMETHEUS_USERNAME` **(string | None)** : If using basic auth, the username to query prometheus with.

`PROMETHEUS_PASSWORD` **(string | None)** : If using basic auth, the password to query prometheus with.

## cgroup-warden
`WARDEN_JOB` **(string)** : The Prometheus scrape job name. Should be 'cgroup-warden'.

`WARDEN_PORT` **(int)** : The port the cgroup-warden is listening on.

`WARDEN_VERIFY_SSL` **(bool)** : If enabled, verify the certificate of the wardens if using TLS.

`WARDEN_USE_TLS` **(bool)** : If enabled, use TLS to make requests to the wardens (https).

`WARDEN_BEARER` **(string | None)** : If given, will be used as the bearer token to authenticate with the cgroup-wardens.

`WARDEN_RUNTIME` **(bool)** : If enabled, the cgroup-warden will not write out persistant drop-in files for limits in `/etc/systemd`, and will instead write these files to `/run`. This means that when enabled, upon reboot all limits will be reset. Arbiter will account for this and sync limits, requiring no action. 

## Email
`ARBITER_NOTIFY_USERS` **(bool)** : If enabled, arbiter will email users about their violations.

`ARBITER_USER_LOOKUP` **(callabe | None)** : A function to lookup a users username, email, and realname given a username. This is a Python function.  

`ARBITER_ADMIN_EMAILS` **(list[string])** : A list of email addresses that arbiter will send all violations to. 

`ARBITER_FROM_EMAIL` **(string)** : The email address arbiter will send mail from.

`ARBITER_EMAIL_TEMPLATE_DIR` **(string | None)** : If given, arbiter will use the templates of `email_body.html` and `email_subject.html` in this dir when sending emails.

`EMAIL_HOST` **(string | None)** : The mail server arbiter will route emails through. 

`EMAIL_PORT` **(int | None)** : The port arbiter will use with the mail server.

`EMAIL_HOST_USER` **(string | None)** If given, arbiter will use this username to authenticate with the mail server.

`EMAIL_HOST_PASSWORD` **(string | None)** If given, arbiter will use this password to authenticate with the mail server.


## Django

The following are Django specific settings. See [here](https://docs.djangoproject.com/en/5.1/topics/settings/) for details on all of the following.

`DEBUG` **(boolean)** : Whether to run the webserver in debug mode.

`DATABASES` **(dict)** : Database configuration.

`SECRET_KEY` **(string)** : A secret used for cryptographic signing and other security purposes.

`ALLOWED_HOSTS` **(list[string])** : A list of host names from which the Arbiter site can be accessed as.

`TIME_ZONE` **(string)** : Time zone used when displaying time.


# Verifying Settings
## Settings File
To verify that the settings are valid, you can run the webserver:
```shell
./arbiter.py runserver 
```
This will throw exceptions if your settings file is improperly configured.

## Email
To verify that emails are working correctly, you can use the `test_email` command with arbiter:
```shell
./arbiter.py test_email --recipients admin1@yoursite.edu admin2@yoursite.edu
``` 
This will send a small test email to the recipients. If the `--violation` flag is included, it will send an example violation email, provided a violation exists in the database.