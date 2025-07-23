### Requirements
Because our warden relies on systemd, we need to use a virtual machine to test it on. In this instance, we will use [Vagrant](https://www.vagrantup.com/) to provision on top of a virtual machine provider, like [VirtualBox](https://www.virtualbox.org/). Please install both applications on your local machine before testing. The testing framework used here is Pytest, and the appropriate Python libraries are installed in the devcontainer. Below is an outline on how to run the tests. 

### Setting up environment
Open a terminal in this directory on your local machine, not in the devcontainer. From here you will run `vagrant up` to start the virtual machine.
Once the machine has been provisioned, you can `vagrant ssh` into the virtual machine. The Vagrant box is provisioned with `testing/vagrant/provisioning.sh`,
which downloads a version of `cgroup-warden` and starts it as a service. 

### Running the tests
There are multiple sets of tests, but they can be all run with
`pytest`
