### Requirements
Because our agent relies on systemd, we need to use a virtual machine to test it on. In this instance, we will use [Vagrant](https://www.vagrantup.com/) to provision on top of a virtual machine provider, like [VirtualBox](https://www.virtualbox.org/). Please install both applications on your local machine before testing. The testing framework used here is Pytest, and the appropriate Python libraries are installed in the devcontainer. Below is an outline on how to run the tests. 

### Setting up environment
Build the binary of the Go project in the devcontainer. This can be done in the testing directory with `go build ..` 
Open a terminal in this directory on your local machine, not in the devcontainer. From here you will run `vagrant up` to start the virtual machine.
Once the machine has been provisioned, you can `vagrant ssh` into the virtual machine.

### Running the tests
There are multiple sets of tests. 
#### Control
For the agent, we run in debug mode. Launch the binary in the vagrant box with

`CGROUP_AGENT_DEBUG=true sudo -E /opt/cgroup-agent/cgroup-agent`

We need sudo to run the binary with priviledge, so we can modify cgroup properties. The `-E` flag ensures the environment variables are passed.
Now we can run the tests. From the devcontainer

`pytest test_control.py`

and 

`pytest test_metrics.py`

#### Authorization
For authorization, we do not run in debug mode, and thus must create certificates. 
In the vagrant box, create an RSA key

`openssl genrsa -out server.key 2048`

Create reate a self-signed certificate from the key

`openssl req -new -x509 -sha256 -key server.key -out server.pem`

This above prompt you, only one field needs to be populated to work.
Run the binary  

`CGROUP_AGENT_SECRET="__UNSAFE__998845161" CGROUP_AGENT_CERTIFICATE=server.pem CGROUP_AGENT_KEY=server.key sudo -E /opt/cgroup-agent/cgroup-agent`

Run the tests in the devcontainer 

`CGROUP_AGENT_SECRET="__UNSAFE__998845161" pytest test_authorization.py`


### Notes
With any changes to the Go project, the binary will have to be built again.

`GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -buildvcs=false ..`