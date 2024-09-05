# Arbiter 3


## Architecture
The architecture for Arbiter 3 involves the follwoing pieces as shown on the diagram below:  
![](resources/architecture.png)

## Development Guide

### Get Arbiter Environment Set up
1. Clone this repository
2. Reopen it inside of a container (if this fails make sure port 9090 is open)
    - The docker configuration files given make 3 containers:
        1. A base conatiner with Python3 and Go to develop/test on
        2. A container that runs a [Prometheus](https://prometheus.io) server as a service which is forwarded to port 9090 on the host machine. So you should be able to see the Prometheus web GUI at `localhost:9090`. This is the Prometheus server Arbiter will talk to to collect user metrics by default.
        3. A container for a Grafana server if you would like to use it for testing (it is not required  for Arbiter to run)
3. Run `poetry shell` inside the container to get inside our python venv
    - If the dependencies are still not installed, you may need to run `poetry install` or `poetry update`
4. If this is your first time running the code, you will want to run `python3 manage.py migrate` to make our db schemas and db file if needed
5. After this you will want to create a super user to use the admin interface, so run `python manage.py createsuperuser` and it will ask you for username/password


### Using Arbiter
1. From here, we can then start the webserver with `python3 manage.py runserver`
2. After you have started the webserver, go to `localhost:8000/admin` in your brower to view the admin page
    - Make sure you have created the superuser as stated above to be able to log in
3. Once in, you can configure the Policies/Penalties you want Arbiter to use and enforce and where.
    - If you want a starting point to work from use `python3 manage.py loaddata start` to load a basic Policy/Penalty in.
    - Note that you will need to set up SystemD Propetries on the admin as well as Limits for them, though you can load the Propetry fixture which is a good starting point using `python3 manage.py loaddata property`
4. Once all the configuration is set up, you can use the Dashboard page on the Admin to see user usage, and run the Arbiter evaluation loop (only one loop) or set Properties on user/hosts with a Cgroup-agent.

5. Now that everything is set up, you can start up the Evaluation loop to run forever, by using `python3 manage.py evaluate` with along with how long you want to wait between each loop using the `--seconds`, `--minutes`, and `--hours` arguments. If no furation arguments are provided, the loop runs once and exits. Additionally, you can specifiy only certain Policies to evaluate if you want using `--policies` and a list of Policy names.
    - If you want to start simple just use this commands which runs the loop every 30 secs `python3 manage.py evaluate --seconds 30`

6. There are also commands for clearing/logs or history. If you want a list of commands run `python3 manage.py` and if you want to know more about a command run `python3 manage.py <command-name> --help`

### Get Cgroup-Agent Testing Environment Set up
1. Because most container runtimes do support systemd, which cgroup-agent utilizes heavily, we opted to use [Vagrant](https://www.vagrantup.com/) to provision virtual machines that we can test the agent on. Before testing make sure you have vagrant as well as a virtual machine provider such as [VirtualBox](https://www.virtualbox.org/). 
2. Now that you have that set up, on your host machine, navigate to /testing in the directory containing this repo and run `vagrant up`. This will set up the vm and run the cgroup-agent as a service. You can verify it is running when the command finishes by going to `localhost:2112/metrics` or if the container is running, by going to `localhost:9090/targets`. 
3. From here you can test how Arbiter will work with the agent by going into the vm with `vagrant ssh` and testing what causes Arbiter's Policies to put you in Penalty.
4. For any adiitional agents you will need to add their host/ip to the `prometheus.yml` in the `.devcontainer/prometheus/` folder. When you do, make sure to add them to the existing `cgroup-agent` job as Arbiter looks for that name.

## Testing
1. To run our test suit you will need to have the container with the Arbiter daemon open, the vagrant vm running with the cgroup-agent up, and the Prometheus server running from its container.
2. Once your vm is up, run in the container's terminal `pytest`
    - Make sure you are in poetry's shell when you do this
3. After running `pytest` you will see the entire test suite running and what passes/fails. This will take some time as many of our tests ssh into the vm box and start "bad behavior" and we wait some time for Promtheus to collect data on this bad behavior then make sure Arbiter does what it is supposed to.
    - Make sure your promtehus scrape interval is low for these tests, roughly around 1sec.
4. After this if you want to test a specific file you can run `pytest <file>` for any of the files in `testing/` where the *Vagrantfile* is located. You can also use `pytest <file>:<test_name>` to run a specific test of `pytest -k <test_regex>` to run all tests that match what you give it.
5. If you want to do any manual tests on your own, it may help to use the grafana server inside the Docker configuration to view usage/limits as you perform specific tests. 
    - To do this naviagte to `localhost:3000` then log in with the default login `username:admin`, `password:admin` which it will ask you to change.
    - From here you can either make your own dashboard or import the serialized one located at `.devcontainer/grafana/dashboard.json`. Make sure to add your Prometheus server as a data source, if it isn't already as well.

## Modeling

We model the Policies and Penalties of the Arbiter Service as the following:
1. A **Property** is a systemd property that can be set on a cgroup.
2. A **Limit** is a vlaue associated with one of those systemd Properties that will be set when a user goes in *Penalty*
3. A **Penalty** is a set of limits (CPU and Memory) and duration that gets applied to a user when a Policy with this penalty gets violated
4. A **Policy** is a *rule* that a user can violate, which will cause a *Violation* to be made with the Policy's repective penalty
6. A **Violation** is an instance of a Violation on a *Target*, or unit-host pairing, which has an associated Penalty and Policy 
5. A **Target** is a user on a specific host that Arbiter monitors usage and penalizes

#### Below are some ER diagrams for the DB schemas we use in the Arbiter daemon if you find them helpful

![](resources/db.jpg)

```mermaid
erDiagram
    Property{
        string name
        Operation operation
        Type type
    }
    Limit{
        string value
    }
    Penalty{
        string name 
        time duration
        float scale_factor
    }
    Policy{
        string name
        string query
        time timewindow
        time lookback
        time grace_period
    }
    Violation{
        int num_offense
        datetime expiration
    }
    Target{
        string unit
        string host
    }
    
    Policy }|--o| Penalty : Enforces
    Target |o--|{ Violation : On
    Violation }|--o| Policy : From
    Property |o--|{ Limit : For
    Penalty }o--o{ Limit : Applies
    Target }o--o{ Limit : Last-Applied
```