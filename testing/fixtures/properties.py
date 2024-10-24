import pytest

@pytest.fixture
def cpu_property():
    return "CPUQuotaPerSecUSec"


@pytest.fixture
def mem_property():
    return "MemoryMax"
