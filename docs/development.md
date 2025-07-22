# Development

## Environment
We use [devcontainers](https://containers.dev/) for our development environment. The following are steps to set the environment up. 
1. Clone this repository
2. Reopen it inside of a container
3. Run `poetry shell` inside the container to get inside our python venv
    - If the dependencies are still not installed, you may need to run `poetry install` or `poetry update`
4. Run `python3 arbiter3/scripts/initialize.py` to initialize configuration files
5. If this is your first time running the code, you will want to run `python3 arbiter.py migrate` to make our db schemas and db file if needed
6. After this you will want to create a super user to use the web interface, so run `python arbiter.py createsuperuser` and it will ask you for username/password

The docker configuration files given make 3 containers:
1. A base container with Python3 and develop/test on
2. A container that runs a [Prometheus](https://prometheus.io) server as a service which is forwarded to port 9090 on the host machine. The Prometheus web GUI is available at `localhost:9090`. This is the Prometheus server Arbiter will talk to to collect user metrics by default.
3. A container for a Grafana server if you would like to use it for testing (it is not required  for Arbiter to run)

## Running Arbiter
Arbiter has two main components, the web server and the evaluation loop.
1. You can start the webserver with `python3 arbiter.py runserver`
2. After you have started the webserver, go to `localhost:8000/` and log in
3. Once in, you can configure the policies you want Arbiter to use and enforce and where.
4. Once all the configuration is set up, you can use the Dashboard page on the Admin to see user usage, and run the Arbiter evaluation loop (only one loop) or set limits on user/hosts with a `cgroup-warden`.
5. Now that everything is set up, you can start up the evaluation loop to run forever, by using `python3 arbiter.py evaluate` with along with how long you want to wait between each loop using the `--seconds`, `--minutes`, and `--hours` arguments. If no furation arguments are provided, the loop runs once and exits. Additionally, you can specifiy only certain Policies to evaluate if you want using `--policies` and a list of Policy names.

## Running cgroup-warden
The following describes how to get a single `cgroup-warden` up for testing. See [TESTING.md](TESTING.md) for details.
1. Open a local terminal (not in devcontainer) 
2. `cd testing/vagrant`
3. `vagrant up`

