# Installing Arbiter 3
Arbiter 3 was created for the Rocky 8 and 9 interactive systems at the Center for High Performance Computing, University of Utah. It can run in other environments, provided the interactive systemds are managed by systemd. In general, the software can be installed by

1. Installing the Arbiter Django Application
2. Installing a Prometheus Instance
3. Installing the cgroup-warden on each interactive node

## Arbiter Django Application
The core arbiter service is a Django application. This needs to be installed on a machine
with secure network access to Prometheus and the desired login nodes.

### Installing Prerequistite Python 3.11
Python 3.11+ is required for the arbiter service. It is likely that your package manager has Python 3.11 available as a package. On Rocky 9.2+, it can be installed with
```shell
sudo dnf install python3.11
```

pip is required as well.
```shell
python3.11 -m ensurepip --default-pip
```

### From here, there are two options for installation:

### Option 1: Install with pip (Recommended)

Start by navigating to the directory where you want arbiter's configuration placed.
```shell
cd /path/to/config_dst
```

Create a virtual environment and then install the arbiter3 PyPi package. 
```shell
python3.11 -m venv venv
source venv/bin/activate
pip install arbiter3
```
This will install the arbiter modules and its dependencies in `venv/lib/source-packages/`, as well as the setup command `arbiter-init`.

### Option 2: Install from Source

First obtain the source code via git
```shell
cd /path/to/install
git clone https://github.com/chpc-uofu/arbiter
cd arbiter
```

Create a virtual environment and install arbiter with pip. 
```shell
python3.11 -m venv venv
source venv/bin/activate
pip install .
```
This will install the arbiter modules and its dependencies in `venv/lib/source-packages/`, as well as the setup command `arbiter-init`.

### Initialize Config
Initialize the default configuration files by running the respective command for your installation method. <u>as the user you wish to run arbiter</u> in your config directory.
```shell
#pip installation
arbiter-init 

#git installation
venv/bin/python3.11 arbiter3/scripts/initialize.py
```

This will generate the following files:

`arbiter.py` - The entry point to run arbiter evaluation loop, webserver, or database management

`settings.py` - The main configuration file for arbiter.

`arbiter-web.service` - A starting point for the service that runs the webserver. 

`arbiter-eval.service` - A starting point for the service that runs the evaluation loop. You may want to adjust how often it evaluates, by default it evaluates usage every 30s

### Configure Settings
The settings for arbiter are configured in the `settings.py` file. This must be configured to run arbiter. See [settings.md](settings.md) for details.

### Initialize Database

```shell
venv/bin/python3.11 arbiter.py migrate
```
This will create all the initial database tables. If using the default database of SQLite, this will create a `db.sqlite3` file. 


### Running the service
The arbiter service has two components, the web server and the core evaluation loop.

#### Web Service
The arbiter web service can be run in a testing capacity with the following command:
```shell
venv/bin/python3.11 arbiter.py runserver 
```
Which will listen on `localhost:8000`. For production, Arbiter should be run with Gunicorn. For example,
```shell
gunicorn arbiter3.portal.wsgi --bind 0.0.0.0:8000 
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
