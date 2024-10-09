import pytest
from arbiter.models import Policy
from fixtures.penalties import *
from datetime import timedelta


CPU_LOW_THRESHOLD = 0.9
MEM_LOW_THRESHOLD = 0.75
CPU_MID_THRESHOLD = 1.9
MEM_MID_THRESHOLD = 1.75


SHORT_WINDOW = timedelta(seconds=10)
SHORT_WINDOW_SEC = 10
MEDIUM_WINDOW = timedelta(seconds=15)


@pytest.fixture
def short_low_harsh_policy(db, harsh_penalty):
    return Policy.objects.create(
        name="short window, low threshold, harsh penalty",
        domain=".*",
        description="description",
        penalty=harsh_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_medium_policy(db, medium_penalty):
    return Policy.objects.create(
        name="short window, low threshold, medium penalty",
        domain=".*",
        description="description",
        penalty=medium_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_soft_policy(db, soft_penalty):
    return Policy.objects.create(
        name="short window, low threshold, soft penalty",
        domain=".*",
        description="description",
        penalty=soft_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_mid_soft_policy(db, soft_penalty):
    return Policy.objects.create(
        name="short window, mid threshold, soft penalty",
        domain=".*",
        description="description",
        penalty=soft_penalty,
        query_params={
            "cpu_threshold": CPU_MID_THRESHOLD,
            "memory_threshold": MEM_MID_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_low_unset_policy(db, unset_penalty):
    return Policy.objects.create(
        name="short window, mid threshold, unset penalty",
        domain=".*",
        description="description",
        penalty=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=0),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def grace_no_lookback_policy(db, unset_penalty):
    return Policy.objects.create(
        name="grace period, short window, mid threshold, unset penalty",
        domain=".*",
        description="description",
        penalty=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=0),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC + 2),
    )


@pytest.fixture
def long_lookback_no_grace_policy(db, unset_penalty):
    return Policy.objects.create(
        name="long lookback, short window, mid threshold, unset penalty",
        domain=".*",
        description="description",
        penalty=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=60),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def short_lookback_no_grace_policy(db, unset_penalty):
    return Policy.objects.create(
        name="short lookback, short window, mid threshold, unset penalty",
        domain=".*",
        description="description",
        penalty=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=SHORT_WINDOW_SEC * 2 + 2),
        grace_period=timedelta(seconds=0),
    )


@pytest.fixture
def long_lookback_with_grace_policy(db, unset_penalty):
    return Policy.objects.create(
        name="long lookback with grace, short window, mid threshold, unset penalty",
        domain=".*",
        description="description",
        penalty=unset_penalty,
        query_params={
            "cpu_threshold": CPU_LOW_THRESHOLD,
            "memory_threshold": MEM_LOW_THRESHOLD,
            "process_whitelist": [],
            "units_whitelist": [],
            "domain": ".*",
        },
        timewindow=SHORT_WINDOW,
        lookback_window=timedelta(seconds=60),
        grace_period=timedelta(seconds=SHORT_WINDOW_SEC // 2),
    )
