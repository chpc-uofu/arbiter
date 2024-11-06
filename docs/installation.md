# Installing Arbiter 3
Arbiter 3 was created for the Rocky 8 and 9 interactive systems at the Center for High Performance Computing, University of Utah. It can run in other environments, provided the interactive systemds are managed by systemd. In general, the software can be installed by

1. Installing the Arbiter Django Application
2. Installing a Prometheus Instance
3. Installing the cgroup-warden on each interactive node

## Arbiter Service
The core arbiter service is a Django application. This needs to be installed on a machine
with secure network access to Prometheus and the desired login nodes.

### Installing Python 3.11
Python 3.11+ is required for the arbiter service. It is likely that your package manager has Python 3.11 available as a package. On Rocky 9.2+, it can be installed with
```shell
sudo dnf install python3.11
```

pip is required as well.
```shell
python3.11 -m ensurepip --default-pip
```

### Installing the source code

First, we would like to specify the installation directory. A reasonable choice is `/opt/arbiter3`, but any directory with the proper permissions may be specified.
```shell
mkdir /opt/arbiter3
```

The Arbiter3 source code should be installed into a virtual environment.
```shell
python3.11 -m venv /opt/arbiter3/venv
/opt/arbiter3/venv/bin/pip install 'arbiter @ git+http://github.com/chpc-uofu/arbiter'
```

This will install Arbiter as a module, as well as all of its dependencies in `arbiter-venv/lib/source-packages/arbiter`.

### Creating a Django Project
Arbiter is a Django app, and must be installed into a Django project to run. To create one,
```shell
/opt/arbiter3/venv/bin/django-admin startproject arbiter_django /opt/arbiter3
```
This will create some additional files such that
```
/opt/arbiter3/
  manage.py
  venv/
    ...
  arbiter_django/
      __init__.py
      settings.py
      urls.py
      asgi.py
      wsgi.py
```

#### Django Configuration
Django relies on the configuration in `settings.py`, which will need to be updated.   
An example settings file is in [`etc/settings.py`](../etc/settings.py).  
See [settings.md](settings.md) for details.

### Running the service
The arbiter service has two components, the web server and the core evaluation loop.

#### Web Service
The arbiter web service can be run in a testing capacity with the following command:
```shell
venv/bin/python manage.py runserver 
```
Which will listen on `localhost:8000`. For production, Arbiter should be run with Gunicorn. For example,
```shell
venv/bin/gunicorn arbiter.wsgi --bind 0.0.0.0:8000 
```
Preferably, this will be set up behind a proxy such as NGINX. 

It should also be set up to run as a systemd service. See an example service file in [`etc/arbiter-wev.service`](../etc/arbiter-web.service)

#### Evaluation Service
The arbiter evaluation loop can be run with
```
venv/bin/python manage.py evaluate
```
To run it in a loop, you can pass the `--seconds`, `--minutes`, or `--hours` flags.

This should also be set up to run as a service, see [`/etc/arbiter-eval.service`](../etc/arbiter-eval.service)


## cgroup-warden
See the [cgroup-warden](https://github.com/chpc-uofu/cgroup-warden/blob/main/INSTALL.md)
installation guide.

## Prometheus
See the [Prometheus](https://prometheus.io/docs/prometheus/latest/installation/) installation guide. 
For general configuration, see [here](https://prometheus.io/docs/prometheus/latest/configuration/). 

Each cgroup-warden instance needs to be scraped. 
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
```