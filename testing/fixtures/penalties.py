import pytest
from arbiter.models import Limit
from fixtures.limits import *
from datetime import timedelta


@pytest.fixture
def harsh_penalty(db, harsh_limit_cpu, harsh_limit_mem):
    # penalty = Penalty.objects.create(
    #     name="harsh_penalty",
    #     duration=timedelta(seconds=5),
    #     repeat_offense_scale=0,
    # )
    # penalty.limits.add(harsh_limit_cpu)
    # penalty.limits.add(harsh_limit_mem)
    return Limit.to_json(harsh_limit_cpu, harsh_limit_mem)


@pytest.fixture
def medium_penalty(db, medium_limit_cpu, medium_limit_mem):
    # penalty = Penalty.objects.create(
    #     name="harsh_penalty",
    #     duration=timedelta(seconds=5),
    #     repeat_offense_scale=0,
    # )
    # penalty.limits.add(medium_limit_cpu)
    # penalty.limits.add(medium_limit_mem)
    return Limit.to_json(medium_limit_cpu, medium_limit_mem)


@pytest.fixture
def soft_penalty(db, soft_limit_cpu, soft_limit_mem):
    # penalty = Penalty.objects.create(
    #     name="harsh_penalty",
    #     duration=timedelta(seconds=10),
    #     repeat_offense_scale=0,
    # )
    # penalty.limits.add(soft_limit_cpu)
    # penalty.limits.add(soft_limit_mem)
    return Limit.to_json(soft_limit_cpu, soft_limit_mem)


@pytest.fixture
def unset_penalty(db, unset_limit_cpu, unset_limit_mem):
    # penalty = Penalty.objects.create(
    #     name="unset_penalty",
    #     duration=timedelta(seconds=10),
    #     repeat_offense_scale=1,
    # )
    # penalty.limits.add(unset_limit_cpu)
    # penalty.limits.add(unset_limit_mem)
    # return penalty
    return Limit.to_json(unset_limit_cpu, unset_limit_mem)
