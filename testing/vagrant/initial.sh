#!/bin/bash

echo "turning on accounting for vagrant user"
sudo systemctl set-property "user-1000.slice" CPUAccounting=true
sudo systemctl set-property "user-1000.slice" MemoryAccounting=true

echo "adding additional users"
for i in 1 2 3 4 5 6
do
    echo "adding user-100$i"
    sudo useradd "user-100$i" -u "100$i" -s /bin/bash
    sudo echo "user-100$i:password" | sudo chpasswd
    sudo systemctl set-property "user-100$i.slice" CPUAccounting=true
    sudo systemctl set-property "user-100$i.slice" MemoryAccounting=true
done

echo "installing stress-ng"
sudo dnf install stress-ng -y

echo "installing git"
sudo dnf install git -y

export GO_VER="1.23.4"
echo "installing go$GO_VER"
curl -OL https://go.dev/dl/go$GO_VER.linux-amd64.tar.gz
tar -xzf go$GO_VER.linux-amd64.tar.gz

echo "creating certificates for https"
openssl req -x509 -newkey rsa:4096 -keyout /vagrant/key.pem -out /vagrant/cert.pem -sha256 -days 3650 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname"

# copy instead of linking because of selinux
echo "copying service file"
sudo cp /vagrant/cgroup-warden/cgroup-warden.service /etc/systemd/system/cgroup-warden.service

echo "cloning repo"
git clone https://github.com/chpc-uofu/cgroup-warden
chown -R vagrant:vagrant cgroup-warden

# default rules block 2112 on rocky8/9, easier to turn it off
echo "turning of firewalld"
systemctl stop firewalld

# default is off on rocky8/9
echo "enabling password ssh"
sed -i "/^[^#]*PasswordAuthentication[[:space:]]no/c\PasswordAuthentication yes" /etc/ssh/sshd_config
systemctl restart sshd

