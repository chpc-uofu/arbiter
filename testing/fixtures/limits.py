import pytest
from arbiter.models import CPU_QUOTA, MEMORY_MAX, UNSET_LIMIT


@pytest.fixture
def unset_limit_cpu():
    return {CPU_QUOTA: UNSET_LIMIT}


@pytest.fixture
def soft_limit_cpu():
    return {CPU_QUOTA: 4000000}  # 4 cores


@pytest.fixture
def medium_limit_cpu():
    return {CPU_QUOTA: 2000000} # 2 cores


@pytest.fixture
def harsh_limit_cpu():
    return {CPU_QUOTA: 1000000}  # 1 core


@pytest.fixture
def unset_limit_mem():
    return {MEMORY_MAX: UNSET_LIMIT}


@pytest.fixture
def soft_limit_mem():
    return {MEMORY_MAX: 4294967296}  # 4 GiB


@pytest.fixture
def medium_limit_mem():
    return {MEMORY_MAX: 2147483648} # 2 GiB


@pytest.fixture
def harsh_limit_mem():
    return {MEMORY_MAX: 1073741824} # 1 GiB