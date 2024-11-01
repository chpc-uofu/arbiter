#!/bin/bash

# turn on accounting for vagrant user
sudo systemctl set-property "user-1000.slice" CPUAccounting=true
sudo systemctl set-property "user-1000.slice" MemoryAccounting=true

# add additional users for running loads under
for i in 1 2 3 4 5 6
do
    sudo useradd "user-100$i" -u "100$i" -s /bin/bash
    sudo echo "user-100$i:password" | sudo chpasswd
    sudo systemctl set-property "user-100$i.slice" CPUAccounting=true
    sudo systemctl set-property "user-100$i.slice" MemoryAccounting=true
done

# install utility for load testing
sudo apt-get install stress-ng -y

# create certificates for https
openssl req -x509 -newkey rsa:4096 -keyout /vagrant/key.pem -out /vagrant/cert.pem -sha256 -days 3650 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname"

# install cgroup-warden
export WAR_VER="0.1.0"
curl -OL https://github.com/chpc-uofu/cgroup-warden/releases/download/v${WAR_VER}/cgroup-warden-linux-amd64-${WAR_VER}.tar.gz
tar -xzf cgroup-warden-linux-amd64-${WAR_VER}.tar.gz
sudo cp cgroup-warden-linux-amd64-${WAR_VER}/cgroup-warden /usr/sbin

# start the cgroup-warden as a service
sudo cp /vagrant/cgroup-warden/cgroup-warden.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable cgroup-warden.service --now
sudo systemctl status cgroup-warden.service