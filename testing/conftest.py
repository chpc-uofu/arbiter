import pytest

from datetime import timedelta

from arbiter3.arbiter.models import Target, Policy, BasePolicy, QueryParameters, QueryData, CPU_QUOTA, MEMORY_MAX, UNSET_LIMIT
from arbiter3.arbiter.utils import BYTES_PER_GIB

from testing.util import unset_limits

# TARGETS
host = "192.168.56.2"


@pytest.fixture()
def target1(db):
    target = Target.objects.create(
        unit="user-1001.slice", host=host, username="user-1001")
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture()
def target2(db):
    target = Target.objects.create(
        unit="user-1002.slice", host=host, username="user-1002")
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture()
def target3(db):
    target = Target.objects.create(
        unit="user-1003.slice", host=host, username="user-1003")
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture()
def target4(db):
    target = Target.objects.create(
        unit="user-1004.slice", host=host, username="user-1004")
    unset_limits(target)
    yield target
    unset_limits(target)


@pytest.fixture()
def target5(db):
    target = Target.objects.create(
        unit="user-1005.slice", host=host, username="user-1005")
    unset_limits(target)
    yield target
    unset_limits(target)


# LIMITS


@pytest.fixture(scope="module")
def unset_limit_cpu():
    return {CPU_QUOTA: UNSET_LIMIT}


@pytest.fixture(scope="module")
def soft_limit_cpu():
    return {CPU_QUOTA: 4000000}  # 4 cores


@pytest.fixture(scope="module")
def medium_limit_cpu():
    return {CPU_QUOTA: 2000000}  # 2 cores


@pytest.fixture(scope="module")
def harsh_limit_cpu():
    return {CPU_QUOTA: 1000000}  # 1 core


@pytest.fixture(scope="module")
def unset_limit_mem():
    return {MEMORY_MAX: UNSET_LIMIT}


@pytest.fixture(scope="module")
def soft_limit_mem():
    return {MEMORY_MAX: 4294967296}  # 4 GiB


@pytest.fixture(scope="module")
def medium_limit_mem():
    return {MEMORY_MAX: 2147483648}  # 2 GiB


@pytest.fixture(scope="module")
def harsh_limit_mem():
    return {MEMORY_MAX: 1073741824}  # 1 GiB


# CONSTRAINTS
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


# PENALTIES
@pytest.fixture
def harsh_penalty(db, harsh_limit_cpu, harsh_limit_mem):
    return {'tiers': [harsh_limit_cpu | harsh_limit_mem]}


@pytest.fixture
def medium_penalty(db, medium_limit_cpu, medium_limit_mem):
    return {'tiers': [medium_limit_cpu | medium_limit_mem]}


@pytest.fixture
def soft_penalty(db, soft_limit_cpu, soft_limit_mem):
    return {'tiers': [soft_limit_cpu | soft_limit_mem]}

@pytest.fixture
def tiered_penalty(db, soft_limit_cpu, soft_limit_mem, medium_limit_cpu, medium_limit_mem, harsh_limit_cpu, harsh_limit_mem):
    return {
        'tiers': [
            soft_limit_cpu | soft_limit_mem, 
            medium_limit_cpu | medium_limit_mem, 
            harsh_limit_cpu | harsh_limit_mem, 
            ]
        }


@pytest.fixture
def unset_penalty(db, unset_limit_cpu, unset_limit_mem):
    return {'tiers': [unset_limit_cpu | unset_limit_mem]}


# POLICIES


CPU_LOW_THRESHOLD = 0.9
MEM_LOW_THRESHOLD = 0.75 * BYTES_PER_GIB
CPU_MID_THRESHOLD = 1.9

DOMAIN = ".*"

SHORT_WINDOW = timedelta(seconds=10)
SHORT_WINDOW_SEC = 10


#----------------------------------
#      Usage policy fixtures
#----------------------------------
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
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=5),
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
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=5),
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
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=10),
        repeated_offense_lookback=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )

@pytest.fixture
def short_low_cpu_policy(db, soft_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=None
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)
    return Policy.objects.create(
        name="short window, low only cpu threshold, soft penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=10),
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
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=10),
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
        repeated_offense_scalar=1.0,
        penalty_duration=timedelta(seconds=10),
        grace_period=timedelta(seconds=0),
    )

@pytest.fixture
def short_low_tiered_policy(db, tiered_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)
    return Policy.objects.create(
        name="short window, low threshold, tiered penalty",
        domain=".*",
        description="description",
        penalty_constraints=tiered_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=60),
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=5),
        grace_period=timedelta(seconds=0),
    )


#----------------------------------
#  Grace+Lookback policy fixtures
#----------------------------------
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
        repeated_offense_scalar=1.0,
        penalty_duration=timedelta(seconds=10),
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
        repeated_offense_scalar=1.0,
        penalty_duration=timedelta(seconds=10),
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
        repeated_offense_scalar=1.0,
        penalty_duration=timedelta(seconds=10),
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
        repeated_offense_scalar=1.0,
        penalty_duration=timedelta(seconds=10),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC // 2),
    )

#----------------------------------
#      Base policy fixtures
#----------------------------------

@pytest.fixture
def base_soft_policy(db, soft_penalty):
    params = None
    query = QueryData.raw_query('cgroup_warden_cpu_usage_seconds{}', params)

    return BasePolicy.objects.create(
        name="base policy soft penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_data=query.json(),
    )

@pytest.fixture
def base_medium_policy(db, medium_penalty):
    params = None
    query = QueryData.raw_query('cgroup_warden_cpu_usage_seconds{}', params)

    return BasePolicy.objects.create(
        name="base policy medium penalty_constraints",
        domain=".*",
        description="description",
        penalty_constraints=medium_penalty,
        query_data=query.json(),
    )


#----------------------------------
#    Whitelist policy fixtures
#----------------------------------
@pytest.fixture
def base_userwhitelist_policy(db, soft_penalty):
    params = QueryParameters(0, 0,  user_whitelist='user-1001')
    query = QueryData.raw_query('cgroup_warden_cpu_usage_seconds{}', params)

    pol = BasePolicy(
        name="base policy soft penalty_constraints user whitelist",
        domain=".*",
        description="description",
        penalty_constraints=soft_penalty,
        query_data=query.json(),
    )
    pol.save()

    return pol

@pytest.fixture
def low_harsh_userwhitelist_policy(db, harsh_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD, user_whitelist='user-1001'
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="short window, low threshold, harsh penalty, user whitelist",
        domain=".*",
        description="description",
        penalty_constraints=harsh_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=5),
        grace_period=timedelta(seconds=0),
    )

@pytest.fixture
def low_harsh_procwhitelist_policy(db, harsh_penalty):
    params = QueryParameters(
        cpu_threshold=CPU_LOW_THRESHOLD, mem_threshold=MEM_LOW_THRESHOLD, proc_whitelist='stress-ng-cpu'
    )
    query = QueryData.build_query(SHORT_WINDOW, DOMAIN, params)

    return Policy.objects.create(
        name="short window, low threshold, harsh penalty, proc whitelist",
        domain=".*",
        description="description",
        penalty_constraints=harsh_penalty,
        query_data=query.json(),
        lookback=SHORT_WINDOW,
        repeated_offense_lookback=timedelta(seconds=0),
        repeated_offense_scalar=0.0,
        penalty_duration=timedelta(seconds=5),
        grace_period=timedelta(seconds=0),
    )
