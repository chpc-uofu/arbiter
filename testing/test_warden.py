from http import HTTPStatus
from time import sleep

from testing.util import create_violation, get_metrics, parse_metrics, set_property_sync

UNSET = -1

MEM_ACCT = "MemoryAccounting"
CPU_ACCT = "CPUAccounting"
MEM_MAX = "MemoryMax"
CPU_SEC = "CPUQuotaPerSecUSec"

WARDEN_METRICS = [
    "cgroup_warden_memory_usage_bytes",
    "cgroup_warden_cpu_usage_seconds",
    "cgroup_warden_proc_count",
    "cgroup_warden_proc_cpu_usage_seconds",
    "cgroup_warden_proc_memory_usage_bytes",
]

def verify(response, code=HTTPStatus.OK):
    assert response.status_code == code
    return response


def test_get_metrics(target1, short_low_harsh_policy):
    runtime = create_violation(target1, short_low_harsh_policy)
    sleep(runtime - 1)
    response = verify(get_metrics(target1))
    metrics = parse_metrics(response.text)
    for metric_name in WARDEN_METRICS:
        assert metric_name in metrics


def test_set_mem_accounting(target1):
    verify(set_property_sync(target1, MEM_ACCT, False))
    verify(set_property_sync(target1, MEM_ACCT, True))


def test_set_cpu_accounting(target1):
    verify(set_property_sync(target1, CPU_ACCT, False))
    verify(set_property_sync(target1, CPU_ACCT, True))


def test_set_mem_limit(target1):
    verify(set_property_sync(target1, MEM_MAX, 800000))
    verify(set_property_sync(target1, MEM_MAX, UNSET))


def test_set_cpu_limit(target1):
    verify(set_property_sync(target1, CPU_SEC, 500000))
    verify(set_property_sync(target1, CPU_SEC, UNSET))


def test_fail_read_only(target1):
    verify(set_property_sync(target1, "MemoryCurrent", 800000), HTTPStatus.BAD_REQUEST)


def test_fail_invalid_property(target1):
    verify(set_property_sync(target1, "NotAProperty", 800000), HTTPStatus.BAD_REQUEST)


def test_fail_invalid_value(target1):
    verify(set_property_sync(target1, "MemoryMax", True), HTTPStatus.BAD_REQUEST)

#TODO implement fail on bad slice

#TODO implement fail on malformed payload