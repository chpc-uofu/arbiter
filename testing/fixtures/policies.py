import pytest
from arbiter.models import Policy, QueryData, QueryParameters
from arbiter.utils import cores_to_nsec, gib_to_bytes
from fixtures.penalties import *
from datetime import timedelta
from .limits import *


CPU_LOW_THRESHOLD = cores_to_nsec(0.9)
MEM_LOW_THRESHOLD = cores_to_nsec(0.75)
CPU_MID_THRESHOLD = cores_to_nsec(1.9)
MEM_MID_THRESHOLD = gib_to_bytes(1.75)

DOMAIN = ".*"

SHORT_WINDOW=timedelta(seconds=10)
SHORT_WINDOW_SEC = 10


@pytest.fixture
def short_low_harsh_policy(db, harsh_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)
    return Policy.objects.create(
        name="short window, low threshold, harsh penalty",
        domain=".*",
        description="description",
        penalty_constraints=harsh_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar = 0.0,
        penalty_duration = timedelta(seconds=5),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_medium_policy(db, medium_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)
    return Policy.objects.create(
        name="short window, low threshold, medium penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=medium_penalty,
        query_data = query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar = 0.0,
        penalty_duration = timedelta(seconds=5),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_soft_policy(db, soft_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)
    return Policy.objects.create(
        name="short window, low threshold, soft penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_data = query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_scalar = 0.0,
        penalty_duration = timedelta(seconds=10),
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_mid_soft_policy(db, soft_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)
    return Policy.objects.create(
        name="short window, mid threshold, soft penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar = 0.0,
        penalty_duration = timedelta(seconds=10),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_unset_policy(db, unset_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar = 1.0,
        penalty_duration = timedelta(seconds=10),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def grace_no_lookback_policy(db, unset_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="grace period, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar = 1.0,
        penalty_duration = timedelta(seconds=10),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC + 2),
    )


@pytest.fixture
def long_lookback_no_grace_policy(db, unset_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="long lookback, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=60),
        repeated_offense_scalar = 1.0,
        penalty_duration = timedelta(seconds=10),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_lookback_no_grace_policy(db, unset_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="short lookback, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=SHORT_WINDOW_SEC * 2 + 2),
        repeated_offense_scalar = 1.0,
        penalty_duration = timedelta(seconds=10),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def long_lookback_with_grace_policy(db, unset_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="long lookback with grace, short window, mid threshold, unset penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=unset_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=60),
        repeated_offense_scalar = 1.0,
        penalty_duration = timedelta(seconds=10),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC // 2),
    )