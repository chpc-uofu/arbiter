import pytest
import requests
import testing.conf
import logging

from arbiter.models import Target

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


def unset_limits(target: Target):
    set_unit_property({"name": "CPUAccounting", "value": True}, target)
    set_unit_property({"name": "MemoryAccounting", "value": True}, target)
    set_unit_property({"name": "MemoryMax", "value": -1}, target)
    set_unit_property({"name": "CPUQuotaPerSecUSec", "value": -1}, target)


@pytest.fixture
def target1(db):
    target = Target.objects.create(unit=testing.conf.TEST_USER1_SLICE, host=testing.conf.TEST_HOST, username=testing.conf.TEST_USER1)
    unset_limits(target)
    yield target
    unset_limits(target)

@pytest.fixture
def target2(db):
    target = Target.objects.create(unit=testing.conf.TEST_USER2_SLICE, host=testing.conf.TEST_HOST, username=testing.conf.TEST_USER2)
    unset_limits(target)
    yield target
    unset_limits(target)

@pytest.fixture
def target3(db):
    target = Target.objects.create(unit=testing.conf.TEST_USER3_SLICE, host=testing.conf.TEST_HOST, username=testing.conf.TEST_USER3)
    unset_limits(target)
    yield target
    unset_limits(target)

@pytest.fixture
def target4(db):
    target = Target.objects.create(unit=testing.conf.TEST_USER4_SLICE, host=testing.conf.TEST_HOST, username=testing.conf.TEST_USER4)
    unset_limits(target)
    yield target
    unset_limits(target)

@pytest.fixture
def target5(db):
    target = Target.objects.create(unit=testing.conf.TEST_USER4_SLICE, host=testing.conf.TEST_HOST, username=testing.conf.TEST_USER5)
    unset_limits(target)
    yield target
    unset_limits(target)