import pytest
from .limits import *


@pytest.fixture
def harsh_constraints(db, harsh_limit_cpu, harsh_limit_mem):
    return [harsh_limit_cpu.json(), harsh_limit_mem.json()]

@pytest.fixture
def medium_constraints(db, medium_limit_cpu, medium_limit_mem):
    return [medium_limit_cpu.json(), medium_limit_mem.json()]

@pytest.fixture
def soft_constraints(db, soft_limit_cpu, soft_limit_mem):
    return [soft_limit_cpu.json(), soft_limit_mem.json()]

@pytest.fixture
def unset_constraints(db, unset_limit_cpu, unset_limit_mem):
    return [unset_limit_cpu.json(), unset_limit_mem.json()]
