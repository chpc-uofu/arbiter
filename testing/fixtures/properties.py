import pytest
from arbiter.models import Property


@pytest.fixture
def cpu_property():
    return Property.objects.create(name="CPUQuotaPerSecUSec", type="int", operation="<")


@pytest.fixture
def mem_property():
    return Property.objects.create(name="MemoryMax", type="int", operation="<")
