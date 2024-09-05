import requests
import pytest
import re
import logging
import http

from testing.conf import *
from testing.test_arbiter import create_violation
from time import sleep

from testing.fixtures.policies import *
from testing.fixtures.limits import *
from testing.fixtures.violations import *
from testing.fixtures.penalties import *
from testing.fixtures.properties import *
from testing.fixtures.targets import *

########## CONSTANT DEFINITIONS ##########


RE_PROM_METRIC = re.compile(r"(?P<metric>.*){(?P<labels>.*)} (?P<value>.*)")
RE_PROM_LABELS = re.compile(r"(?P<label>.*)=\"(?P<tag>.*)\"")

GIB = 1024**3
MIB = 1024**2
UNSET = -1

PROPERTIES = [
    "MemoryAccounting",
    "CPUAccounting",
    "MemoryMax",
    "CPUQuotaPerSecUSec",
]

SYSTEMD_METRICS = [
    "systemd_unit_memory_accounting",
    "systemd_unit_cpu_accounting",
    "systemd_unit_memory_max_bytes",
    "systemd_unit_memory_current_bytes",
    "systemd_unit_cpu_quota_ns_per_s",
    "systemd_unit_cpu_usage_ns",
    "systemd_unit_proc_cpu_seconds",
    "systemd_unit_proc_memory_bytes",
    "systemd_unit_proc_count",
]

########## GLOBAL DECLARATIONS ##########
logger = logging.getLogger(__name__)


########## HELPER FUNCTIONS ##########
def set_property(property, name, value):
    payload = {
        name: value,
        "property": property,
        "runtime": False,
    }
    headers = {"Authorization": TEST_BEARER_TOKEN}
    response = requests.post(
        TEST_CONTROL_ENDPOINT, json=payload, headers=headers, verify=False
    )
    return response


def set_unit_property(property):
    return set_property(property, name="unit", value=TEST_USER1_SLICE)

def set_and_verify_unit_property(property):
    response = set_property(property, name="unit", value=TEST_USER1_SLICE)
    assert response.status_code == http.HTTPStatus.OK
    data = response.json()
    assert data["username"] == TEST_USER1
    assert data["unit"] == TEST_USER1_SLICE
    assert data["property"] == property

def set_and_fail_unit_property(property):
    response = set_property(property, name="unit", value=TEST_USER1_SLICE)
    assert response.status_code == http.HTTPStatus.BAD_REQUEST


def set_and_verify_username_property(property):
    response = set_property(property, name="username", value=TEST_USER1)
    assert response.status_code == http.HTTPStatus.OK


def parse_metrics(data):
    metrics = {}
    for line in data.splitlines():
        if line.startswith("#"):
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


########## TESTING FUNCTIONS ##########

def test_get_metrics(target1, short_low_harsh_policy):
    runtime = create_violation(target1, short_low_harsh_policy)
    sleep(runtime-1)
    response = requests.get(TEST_METRICS_ENDPOINT, verify=False)
    assert response.status_code == http.HTTPStatus.OK, response.text
    metrics = parse_metrics(response.text)
    for metric_name in SYSTEMD_METRICS:
        assert metric_name in metrics

def test_set_with_username():
    set_and_verify_username_property({"name": "MemoryAccounting", "value": "false"})
    set_and_verify_username_property({"name": "MemoryAccounting", "value": "true"})

def test_set_mem_accounting():
    set_and_verify_unit_property({"name": "MemoryAccounting", "value": "false"})
    set_and_verify_unit_property({"name": "MemoryAccounting", "value": "true"})

def test_set_cpu_accounting():
    set_and_verify_unit_property({"name": "CPUAccounting", "value": "false"})
    set_and_verify_unit_property({"name": "CPUAccounting", "value": "true"})

def test_set_mem_limit():
    set_and_verify_unit_property({"name": "MemoryMax", "value": str(8 * GIB)})
    set_and_verify_unit_property({"name": "MemoryMax", "value": str(UNSET)})
    
def test_set_cpu_limit():
    set_and_verify_unit_property({"name": "CPUQuotaPerSecUSec", "value": "500000"})
    set_and_verify_unit_property({"name": "CPUQuotaPerSecUSec", "value": str(UNSET)})
    
def test_fail_read_only():
    set_and_fail_unit_property({"name": "MemoryCurrent", "value": "800000"})

def test_fail_invalid_property():
    set_and_fail_unit_property({"name": "NotAProperty", "value": "800000"})

def test_fail_invalid_value():
    set_and_fail_unit_property({"name": "MemoryMax", "value": "true"})

def test_fail_write():
    property = {"name": "MemoryMax", "value": "800000"}
    payload = {
        "unit": "NotASlice",
        "property": property,
        "runtime": False,
    }
    headers = {"Authorization": TEST_BEARER_TOKEN}
    r = requests.post(
        TEST_CONTROL_ENDPOINT, headers=headers, json=payload, verify=False
    )
    assert r.status_code == http.HTTPStatus.BAD_REQUEST

def test_fail_malformed():
    headers = {"Authorization": TEST_BEARER_TOKEN}
    r = requests.post(
        TEST_CONTROL_ENDPOINT, headers=headers, data="Hello, world!", verify=False
    )
    assert r.status_code == http.HTTPStatus.BAD_REQUEST

def test_malformed_target():
    property = {"name": "MemoryMax", "value": "800000"}
    response = set_property(property, name="bad", value=TEST_USER1_SLICE)
    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    
    response = set_property(property, name="username", value="NOT FOUND")
    assert response.status_code == http.HTTPStatus.BAD_REQUEST