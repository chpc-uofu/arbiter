# Settings
The Arbiter Django app is configured with in the `config.toml` file.  
## `[django]`
`debug` (boolean, default=true)
- Whether to run the Django server in debug mode.
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#debug)

`allowed_hosts` (list of string, default=['localhost'])
- A list of hostnames from which the Arbiter site can be accessed from.
- Should be set to the fully qualified domain name of the server running arbiter. 
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#allowed-hosts)

`secret_key` (string, required)
- A secret used for cryptographic signing and other security purposes.
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#secret-key)

`time_zone` (string, default='UTC')  
- Time zone used when displaying time.
- Should be set to your local timezone.
- [Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#time-zone)

## `[general]`
`min_uid` (integer, default=1000)  
- Arbiter will ignore all accounts with a uid less than this number.

`permissive_mode` (boolean, default=False)
- If enabled, Arbiter will not set resource limits.

## `[email]`

`notify_users` (boolean, default=True)
- If enabled, Arbiter will send emails to users.
- Emails and users are resolved with the `lookup_function`. 

`lookup_function` (string, default='arbiter.utils.default_user_lookup')
- Path to Python function that will resolve a user. 
- For API, see `default_user_lookup` in [`utils.py`](../arbiter/utils.py)

`host` (string, required if `notify_users`)  
- Address of your mail server.

`port` (string, default='25')  
- Port the mail server is listening to requests on.

`domain` (string, required if default `lookup_function` is used)
- Used as part of the default user lookup function. 
- Email is `username@domain`. 

## `[prometheus]`
`url` (string, required)
- URL of your prometheus instance that scrapes the wardens.

`verify_ssl` (boolean, default=True)
- If enabled, arbiter will verify the certificate of your prometheus instance if using TLS.

`user` (string, optional)
- If given, will be used as part of the basic auth with your prometheus instance.

`password` (string, optional)
- If given, will be used as part of the basic auth with your prometheus instance.

`scrape_interval` (integer, required)  
- The interval at which Prometheus scrapes the cgroup-wardens in seconds, must match the value in prometheus scrape configuration.

## `[warden]`
`job` (string, default='cgroup-warden')
- The name of the prometheus scrape job that collects cgroup-warden data.

`port` (string, default='2112')
- The port that your wardens listen on. 

`verify_ssl` (boolean, default=true)
- If enabled, verify the certificate of the wardens if using TLS.

`use_tls` (boolean, default=true)
- If enabled, use TLS to make requests to the wardens (https).

`bearer` (string, optional)
- If given, will be used as the bearer token to authenticate with the wardens