import pytest
from arbiter.models import Policy, Query, QueryParameters
from datetime import timedelta
from .limits import *
from .constraints import harsh_constraints


CPU_LOW_THRESHOLD = 0.9
MEM_LOW_THRESHOLD = 0.75
CPU_MID_THRESHOLD = 1.9
MEM_MID_THRESHOLD = 1.75

NO_DURATION = timedelta(seconds=0)
SHORT_DURATION = timedelta(seconds=5)
LONG_DURATION = timedelta(seconds=10)

DOMAIN = ".*"
DESCRIPTION = "description"

LOW_THRESHOLD_PARAMS = QueryParameters(proc_whitelist=None, user_whitelist=None, cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD)
MID_THRESHOLD_PARAMS = QueryParameters(proc_whitelist=None, user_whitelist=None, cpu_threshold=CPU_MID_THRESHOLD, mem_threshold=MEM_MID_THRESHOLD)


@pytest.fixture
def short_low_harsh_policy(db, harsh_constraints):
    return Policy.objects.create(
        is_base_policy = False,
        name="short window, low threshold, harsh constraints",
        domain=DOMAIN,
        lookback=SHORT_DURATION,
        penalty_constraints=harsh_constraints,
        penalty_duration=SHORT_DURATION,
        repeated_offense_scalar=0,
        repeated_offense_lookback=NO_DURATION,
        grace_period=NO_DURATION,
        query = Query.build_query(SHORT_DURATION, DOMAIN, LOW_THRESHOLD_PARAMS).json()
    )

""""

@pytest.fixture
def short_low_medium_policy(db, medium_penalty):
    return Policy.objects.create(
        name="short window, low threshold, medium penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=medium_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_soft_policy(db, soft_penalty):
    return Policy.objects.create(
        name="short window, low threshold, soft penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_mid_soft_policy(db, soft_penalty):
    return Policy.objects.create(
        name="short window, mid threshold, soft penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_params={
            "cpu_threshold": CPU_MID_THRESHOLD,
            "memory_threshold": MEM_MID_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_unset_policy(db, unset_penalty):
    return Policy.objects.create(
        name="short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def grace_no_lookback_policy(db, unset_penalty):
    return Policy.objects.create(
        name="grace period, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC + 2),
    )


@pytest.fixture
def long_lookback_no_grace_policy(db, unset_penalty):
    return Policy.objects.create(
        name="long lookback, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=60),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_lookback_no_grace_policy(db, unset_penalty):
    return Policy.objects.create(
        name="short lookback, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=SHORT_WINDOW_SEC * 2 + 2),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def long_lookback_with_grace_policy(db, unset_penalty):
    return Policy.objects.create(
        name="long lookback with grace, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=60),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC // 2),
    )

"""