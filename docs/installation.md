# Installing Arbiter 3
Arbiter 3 was created for the Rocky 8 and 9 interactive systems at the Center for High Performance Computing, University of Utah. It can run in other environments, provided the interactive systemds are managed by systemd. In general, the software can be installed by

1. Installing the Arbiter Django Application
2. Installing a Prometheus Instance
3. Installing the cgroup-warden on each interactive node

## Arbiter Service
The core arbiter service is a Django application. This needs to be installed on a machine
with secure network access to Prometheus and the desired login nodes.

### Creating Arbiter service account
Arbiter needs to run under a service account.
```shell
groupadd arbiter
useradd -d /srv/arbiter -s /bin/false arbiter -g arbiter
```

### Installing Python 3.11
Python 3.11+ is required for the arbiter service, as is pip. 

#### Installing from repositories
It is likely that your package manager has Python 3.11 available as a package. On Rocky 9.2+
```shell
sudo dnf install python3.11
```

pip is required as well.
```shell
python3.11 -m ensurepip --default-pip
```

### Installing source
```shell
python3.11 -m pip install
```

### Running the service
The arbiter service has two components, the web server and the core evaluation loop. 

## cgroup-warden

### Install
See the [cgroup-warden](https://github.com/chpc-uofu/cgroup-warden/blob/main/INSTALL.md)
installation guide.

### Configure
See the [cgroup-warden](https://github.com/chpc-uofu/cgroup-warden/blob/main/INSTALL.md#configure)
installation guide.

## Prometheus
### Install
See the [Prometheus](https://prometheus.io/docs/prometheus/latest/installation/) installation guide. 

### Configure
For general configuration, see [here](https://prometheus.io/docs/prometheus/latest/configuration/). 

Each cgroup-warden instance needs to be scraped. An example configuration might be
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