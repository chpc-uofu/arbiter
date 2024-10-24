import pytest
from arbiter.models import Limit

from testing.fixtures.properties import cpu_property, mem_property


@pytest.fixture
def unset_limit_cpu(cpu_property):
    return Limit.cpu_quota(-1)


@pytest.fixture
def soft_limit_cpu(cpu_property):
    return Limit.cpu_quota(4000000)  # 4 cores


@pytest.fixture
def medium_limit_cpu(cpu_property):
    return Limit.cpu_quota(2000000)  # 2 cores


@pytest.fixture
def harsh_limit_cpu(cpu_property):
    return Limit.cpu_quota(1000000)  # 1 core


@pytest.fixture
def unset_limit_mem(mem_property):
    return Limit.memory_max(-1)  # 4 GiB


@pytest.fixture
def soft_limit_mem(mem_property):
    return Limit.memory_max(4294967296)  # 4 GiB


@pytest.fixture
def medium_limit_mem(mem_property):
    return Limit.memory_max(2147483648)  # 2 GiB


@pytest.fixture
def harsh_limit_mem(mem_property):
    return Limit.memory_max(1073741824)  # 1 GiB


@pytest.fixture
def many_limit_cpu(db, harsh_limit_cpu, medium_limit_cpu, soft_limit_cpu):
    return [harsh_limit_cpu, medium_limit_cpu, soft_limit_cpu]

@pytest.fixture
def many_limit_mem(db, harsh_limit_mem, medium_limit_mem, soft_limit_mem):
    return [harsh_limit_mem, medium_limit_mem, soft_limit_mem]
