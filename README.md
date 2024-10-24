[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

<img src="resources/arbiter.png" width="150px" />

# Arbiter 3 
**Arbiter 3 is currently in beta. Feel free play around with Arbiter, but know
that there will be issues. When you encounter them, please open an issue on GitHub, or better yet, submit a PR. See [CONTRIBUTING.md](CONTRIBUTING.md) for details**

Arbiter 3 is a system of software created to monitor and manage resource usage on 
HPC cluster login nodes. A successor of [Arbiter2](https://github.com/chpc-uofu/arbiter2), it aims to be easier to configure and deploy. 

## Architecture
Arbiter 3 is composed of three main components: the Prometheus time-series database (TSDB), the Python Arbiter service, and the cgroup-wardens running on login nodes.
The wardens expose user usage via https, which can then be ingested into Prometheus. The Arbiter service queries the TSDB for user usage data, and creates violations
of pre-defined policies. Arbiter then sends RPC calls, again over https, to the wardens affected by the policy violation, setting hard limits on user resources. Arbiter
also evaluates the state of violations (to possibly expire them), and sends emails to users regarding their violations. 

<img src="resources/architecture.png"/>
