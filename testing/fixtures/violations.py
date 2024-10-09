import pytest
from arbiter.models import Violation, Target
from fixtures.policies import short_low_harsh_policy
from datetime import datetime
from django.utils.timezone import make_aware


@pytest.fixture
def harsh_mixed_violation(db, short_low_harsh_policy):
    target = Target.objects.create(
        unit="user-random.slice", host="some.random.host"
    )
    return Violation.objects.create(
        target=target,
        policy=short_low_harsh_policy,
        expiration=make_aware(datetime.now())
        + short_low_harsh_policy.penalty.duration,
    )
