import paramiko
import requests
import math
import django
import multiprocessing
import re

from arbiter3.arbiter.models import Target, Policy, Violation
from arbiter3.arbiter.conf import WARDEN_USE_TLS, WARDEN_PORT, WARDEN_BEARER, WARDEN_VERIFY_SSL
from arbiter3.arbiter.utils import bytes_to_gib


RE_PROM_METRIC = re.compile(r"(?P<metric>.*){(?P<labels>.*)} (?P<value>.*)")
RE_PROM_LABELS = re.compile(r"(?P<label>.*)=\"(?P<tag>.*)\"")


def parse_metrics(data):
    metrics = {}
    for line in data.splitlines():
        if not line.startswith('cgroup_warden'):
            continue
        metric_matches = RE_PROM_METRIC.match(line)
        metric = metric_matches.group("metric")
        value = metric_matches.group("value")
        label_dict = {}
        label_dict["value"] = value
        for label_string in metric_matches.group("labels").split(","):
            label_matches = RE_PROM_LABELS.match(label_string)
            label = label_matches.group("label")
            tag = label_matches.group("tag")
            label_dict[label] = tag
        if metric in metrics.keys():
            metrics[metric].append(label_dict)
        else:
            metrics[metric] = [label_dict]

    return metrics


def set_property_sync(target: Target, name: str, value: any):
    if WARDEN_USE_TLS:
        endpoint = f"https://{target.host}:{WARDEN_PORT}/control"
    else:
        endpoint = f"http://{target.host}:{WARDEN_PORT}/control"

    payload = {"unit": target.unit, "property": {'name': name, 'value': value}}

    if WARDEN_BEARER:
        auth_header = {"Authorization": "Bearer " + WARDEN_BEARER}
    else:
        auth_header = None

    response = requests.post(
        url=endpoint,
        json=payload,
        timeout=5,
        headers=auth_header,
        verify=WARDEN_VERIFY_SSL,
    )

    return response


def get_metrics(target: Target):
    if WARDEN_USE_TLS:
        endpoint = f"https://{target.host}:{WARDEN_PORT}/metrics"
    else:
        endpoint = f"http://{target.host}:{WARDEN_PORT}/metrics"

    response = requests.get(url=endpoint, verify=WARDEN_VERIFY_SSL)
    return response


def unset_limits(target: Target):
    set_property_sync(target, "CPUAccounting", True)
    set_property_sync(target, "MemoryAccounting", True)
    set_property_sync(target, "CPUQuotaPerSecUSec", -1)
    set_property_sync(target, "MemoryMax", -1)


def launch_ssh_process(target: Target, command: str, password: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        target.host,
        username=target.username,
        password=password,
        allow_agent=False,
    )
    stdin, stdout, stderr = ssh.exec_command(command)
    stdin.close()
    assert stderr.channel.recv_exit_status() == 0


def create_violating_command(policy: Policy) -> str:
    #base policy just be logged in for 5 sec
    if policy.is_base_policy:
        return "sleep 5"
    
    command = "stress-ng"
    cpu = policy.query_data.get("params", {}).get("cpu_threshold", None)
    if cpu:
        command += f" --cpu {math.ceil(cpu)}"
    mem = policy.query_data.get("params", {}).get("mem_threshold", None)
    if mem:
        command += f" --vm 1 --vm-bytes {math.ceil(bytes_to_gib(mem))}g --vm-populate --vm-keep --vm-madvise willneed"
    time = int(policy.lookback.total_seconds())
    if not time:
        time = 10
    command += f" --timeout {time}s"

    return command


def get_violations(target: Target):
    now_tz = django.utils.timezone.make_aware(
        django.utils.timezone.datetime.now())
    violations = Violation.objects.filter(
        unit=target.unit,
        host=target.host,
        expiration__gt=now_tz,
    )
    return violations


def create_violation(target, policy: Policy):
    password = "password"
    comm = create_violating_command(policy)
    if policy.is_base_policy:
        window = 5
    else:
        window = int(policy.lookback.total_seconds())
    user = target.unit.split(".")[0]
    p = multiprocessing.Process(
        target=launch_ssh_process, args=(target, comm, password))
    p.start()
    return window + 1


def duration(policy):
    if policy.is_base_policy:
        return 6
    else:
        return int(policy.penalty_duration.total_seconds()) + 1
