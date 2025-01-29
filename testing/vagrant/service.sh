#!/bin/bash

echo "stopping service"
sudo systemctl stop cgroup-warden.service

echo "building binary"
go/bin/go build -C cgroup-warden

echo "copying binary to /usr/bin"
cp cgroup-warden/cgroup-warden /usr/bin/cgroup-warden

echo "starting service"
sudo systemctl daemon-reload
sudo systemctl enable cgroup-warden.service --now
sudo systemctl status cgroup-warden.service