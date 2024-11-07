import pytest
from fixtures.limits import *
from datetime import timedelta

@pytest.fixture
def harsh_penalty(db, harsh_limit_cpu, harsh_limit_mem):
    return harsh_limit_cpu | harsh_limit_mem


@pytest.fixture
def medium_penalty(db, medium_limit_cpu, medium_limit_mem):
    return medium_limit_cpu | medium_limit_mem


@pytest.fixture
def soft_penalty(db, soft_limit_cpu, soft_limit_mem):
    return soft_limit_cpu | soft_limit_mem


@pytest.fixture
def unset_penalty(db, unset_limit_cpu, unset_limit_mem):
    return unset_limit_cpu | unset_limit_mem
