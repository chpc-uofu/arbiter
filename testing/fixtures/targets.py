import pytest
import requests
import testing.conf
import collections
import logging

TargetTuple = collections.namedtuple("Target", ["unit", "host"])

logger = logging.getLogger(__name__)


def set_unit_property(property, target):
    response = requests.post(
        url=testing.conf.TEST_CONTROL_ENDPOINT,
        json={
            "unit": target.unit,
            "property": property,
            "runtime": False,
        },
        headers={
            "Authorization": testing.conf.TEST_BEARER_TOKEN,
        },
        verify=False,
        timeout=5,
    )
    return response


def unset_limits(target):
    set_unit_property({"name": "CPUAccounting", "value": "true"}, target)
    set_unit_property({"name": "MemoryAccounting", "value": "true"}, target)
    set_unit_property({"name": "MemoryMax", "value": "-1"}, target)
    set_unit_property({"name": "CPUQuotaPerSecUSec", "value": "-1"}, target)


@pytest.fixture
def target1():
    target = TargetTuple(testing.conf.TEST_USER1_SLICE, testing.conf.TEST_HOST)
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture
def target2():
    target = TargetTuple(testing.conf.TEST_USER2_SLICE, testing.conf.TEST_HOST)
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture
def target3():
    target = TargetTuple(testing.conf.TEST_USER3_SLICE, testing.conf.TEST_HOST)
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture
def target4():
    target = TargetTuple(testing.conf.TEST_USER4_SLICE, testing.conf.TEST_HOST)
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture
def target5():
    target = TargetTuple(testing.conf.TEST_USER5_SLICE, testing.conf.TEST_HOST)
    unset_limits(target)
    yield target
    unset_limits(target)
