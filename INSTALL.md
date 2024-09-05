# Installation Guide

The installation of Arbiter 3 is as follows:
1. Install and configure the arbiter Django app
2. Install and configure Prometheus
3. Install and configure cgroup-warden on each login node

## Arbiter Service
The core arbiter service is a Django application. This needs to be installed on a machine
with secure network access to Prometheus and the desired login nodes.

### Requirements
- Python 3.11+
- SQLite3 (or another Django compatible DB backend)

### Install
...
### Configure
...

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