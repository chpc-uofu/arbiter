# Installing Arbiter 3
Arbiter 3 was created for the Rocky 8 and 9 interactive systems at the Center for High Performance Computing, University of Utah. It can run in other environments, provided the interactive systemds are managed by systemd. In general, the software can be installed by

1. Installing the Arbiter Django Application
2. Installing a Prometheus Instance
3. Installing the cgroup-warden on each interactive node

## Arbiter Django Application
The core arbiter service is a Django application. This needs to be installed on a machine
with secure network access to Prometheus and the desired login nodes.

### Install Python 3.11
Python 3.11+ is required for the arbiter service. It is likely that your package manager has Python 3.11 available as a package. On Rocky 9.2+, it can be installed with
```shell
sudo dnf install python3.11
```

### Install Source Code
We can then install the project and its dependencies using `pip`. It should be installed into a virtual environment, like 

```shell
python3.11 -m venv venv
venv/bin/python3.11 pip install arbiter3
```
This will install the arbiter modules and its dependencies in `venv/lib/source-packages/`, as well as the setup command `arbiter-init`.

### Initialize Config

To initialize the arbiter configuration, run the init program:
```
venv/bin/arbiter-init
```
This will create four files: `manage.py`, `settings.py`, `arbiter-eval.serivce`, and `arbiter-web.service`.


### Configure Settings
The settings for arbiter are configured in the `settings.py` file. This must be configured to run arbiter. See [settings.md](settings.md) for details.

### Initialize Database

```shell
venv/bin/python3.11 ./manage.py migrate
```
This will create all the initial database tables. If using the default database of SQLite, this will create a `db.sqlite3` file. 


### Running the service
The arbiter service has two components, the web server and the core evaluation loop.

#### Web Service
The arbiter web service can be run in a testing capacity with the following command:
```shell
./manage.py runserver 
```
Which will listen on `localhost:8000`. For production, Arbiter should be run with Gunicorn. For example,
```shell
gunicorn portal.wsgi --bind 0.0.0.0:8000 
```
Preferably, this will be set up behind a proxy such as NGINX. 

An Example for running this as a service were generated with `arbiter-init`, located in `arbiter-web.service`. Update this to suite your needs. 

#### Evaluation Service
The arbiter evaluation loop can be run with
```
./manage.py evaluate
```
To run it in a loop, you can pass the `--seconds`, `--minutes`, or `--hours` flags.

This should also be set up to run as a service, see `arbiter-eval.service`.


## cgroup-warden
See the [cgroup-warden](https://github.com/chpc-uofu/cgroup-warden)
installation guide.

It is highly recommended to communicate with cgroup-wardens in secure mode.
Each warden must be configured to use TLS and bearer token auth, and arbiter must be configured to reflect this by modifying
`verify_ssl`, `use_tls`, and `bearer` in the [configuration](https://github.com/chpc-uofu/arbiter/blob/main/docs/settings.md#warden)


## Prometheus
See the [Prometheus](https://prometheus.io/docs/prometheus/latest/installation/) installation guide. 
For general configuration, see [here](https://prometheus.io/docs/prometheus/latest/configuration/). 

Each cgroup-warden instance needs to be scraped. The job looks like:
```yaml
scrape_configs:
  - job_name: 'cgroup-warden'
    scrape_interval: 30s
    static_configs:
      - targets:
        - login1.yoursite.edu:2112
        - login2.yoursite.edu:2112
        - login3.yoursite.edu:2112
        - login4.yoursite.edu:2112
    scheme: https

    # recommended but optional, strip port from instance
    relabel_configs:
      - source_labels: [__address__]
        target_label: __address__
        regex: '^(.*):[0-9]+$'
        replacement: '${1}'
```

- The recommended value of `scrape_interval` is `30s`. 
- The job name **must** be `cgroup-warden` or have it as a prefix. 
