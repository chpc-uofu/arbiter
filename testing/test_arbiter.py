import time
import pytest
import multiprocessing
import paramiko
import logging
import math

import django.db.models
import django.utils.timezone

import arbiter.models
import arbiter.eval
from arbiter.utils import bytes_to_gib
from arbiter.models import Target, Violation

from testing.conf import *


from testing.conf import *
from testing.fixtures.policies import *
from testing.fixtures.limits import *
from testing.fixtures.penalties import *
from testing.fixtures.targets import *


logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.WARNING)


# @pytest.fixture
# def global_eval_cache():
#     arbiter.eval.cache.clear()
#     yield arbiter.eval.cache
#     arbiter.eval.cache.clear()


########## HELPER FUNCTIONS ##########
def launch_ssh_process(comm: str, user: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        TEST_ADDRESS,
        username=user,
        password=TEST_USER_PASSWORD,
        allow_agent=False,
    )
    stdin, stdout, stderr = ssh.exec_command(comm)
    stdin.close()
    assert stderr.channel.recv_exit_status() == 0


def create_violating_command(policy: arbiter.models.Policy) -> str:
    command = "stress-ng"
    cpu = policy.query_data.get("params", {}).get("cpu_threshold", None)
    if cpu:
        command += f" --cpu {math.ceil(cpu)}"
    mem = policy.query_data.get("params", {}).get("mem_threshold", None)
    if mem:
        command += f" --vm 1 --vm-bytes {math.ceil(bytes_to_gib(mem))}g --vm-populate --vm-keep --vm-madvise willneed"
    time = int(policy.lookback.total_seconds())
    if not time:
        time = 10
    command += f" --timeout {time}s"
    return command


def get_violations(target: arbiter.eval.Target):
    now_tz = django.utils.timezone.make_aware(django.utils.timezone.datetime.now())
    violations = arbiter.models.Violation.objects.filter(
        unit=target.unit,
        host=target.host,
        expiration__gt=now_tz,
    )
    return violations


def create_violation(target, policy):
    comm = create_violating_command(policy)
    window = int(policy.lookback.total_seconds())
    user = target.unit.split(".")[0]
    p = multiprocessing.Process(target=launch_ssh_process, args=(comm, user))
    p.start()
    return window + 1


def duration(policy):
    return int(policy.penalty_duration.total_seconds()) + 1


##################################################
#                   Core Tests                   #
# (Policy overlap, removal after expiration,     #
# harshest limits applied when policies overlap) #
##################################################
@pytest.mark.django_db(transaction=True)
def test_single_target_single_policy(short_low_harsh_policy, target1):
    # start bad behavior
    runtime = create_violation(target1, short_low_harsh_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    arbiter.eval.evaluate([short_low_harsh_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None  # here

    # make sure correct limits were applied
    should_be = short_low_harsh_policy.penalty_constraints
    assert db_target1.limits == should_be

    # now wait out violation and make sure limits were removed
    time.sleep(duration(short_low_harsh_policy))
    arbiter.eval.evaluate([short_low_harsh_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None

    # make sure target has no limits applied
    assert len(db_target1.limits) == 0


@pytest.mark.django_db(transaction=True)
def test_single_target_overlapping_policy(
    short_low_harsh_policy,
    short_low_medium_policy,
    target1,
):
    # start bad behavior
    runtime = create_violation(target1, short_low_harsh_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    arbiter.eval.evaluate([short_low_harsh_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints
    assert db_target1.limits == should_be

    # now wait out violation
    waiting = max(duration(short_low_harsh_policy), duration(short_low_medium_policy))
    time.sleep(waiting)

    # eval and make sure limits were removed
    arbiter.eval.evaluate([short_low_harsh_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    assert len(db_target1.limits) == 0


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_multiple_target_single_policy(
    short_low_harsh_policy,
    target1,
    target2,
):
    # start bad behvaior for both targets
    runtime1 = create_violation(target1, short_low_harsh_policy)
    runtime2 = create_violation(target2, short_low_harsh_policy)
    time.sleep(max(runtime1, runtime2))

    # evaluate and grab db targets
    arbiter.eval.evaluate([short_low_harsh_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target1 != None
    assert db_target2 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints
    assert db_target1.limits == should_be
    assert db_target2.limits == should_be

    # now wait out violation and re-evaluate
    time.sleep(duration(short_low_harsh_policy))
    arbiter.eval.evaluate([short_low_harsh_policy])

    # make sure limits got removed
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target1 != None
    assert db_target2 != None
    assert len(db_target1.limits) == 0
    assert len(db_target2.limits) == 0


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_multiple_target_multiple_overlapping_policy(
    short_low_harsh_policy,
    short_low_medium_policy,
    target1,
    target2,
):
    # start bad behvaior for both targets
    runtime1 = create_violation(target1, short_low_harsh_policy)
    runtime2 = create_violation(target2, short_low_harsh_policy)
    time.sleep(max(runtime1, runtime2))

    # evaluate and grab db targets
    arbiter.eval.evaluate([short_low_harsh_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target1 != None
    assert db_target2 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints
    assert db_target1.limits == should_be
    assert db_target2.limits == should_be

    # now wait out violation and re-evaluate
    time.sleep(max(duration(short_low_harsh_policy), duration(short_low_medium_policy)))
    arbiter.eval.evaluate([short_low_harsh_policy, short_low_medium_policy])

    # make sure limits got removed
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target1 != None
    assert db_target2 != None
    assert len(db_target1.limits) == 0
    assert len(db_target2.limits) == 0


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_single_target_distinct_policy(
    short_low_harsh_policy,
    short_mid_soft_policy,
    target1,
):
    # start bad behvaior for target
    runtime = create_violation(target1, short_low_harsh_policy)
    time.sleep(runtime)
    
    # evaluate and grab db target
    arbiter.eval.evaluate([short_low_harsh_policy, short_mid_soft_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints
    assert db_target1.limits == should_be

    # now wait out harsh violation and re-evaluate
    time.sleep(duration(short_low_harsh_policy))
    arbiter.eval.evaluate([short_low_harsh_policy, short_mid_soft_policy])

    # penalty for violation of soft policy has a longer duration, so it is still active
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    should_be = short_mid_soft_policy.penalty_constraints
    assert db_target1.limits == should_be


#############################################################
#                        Grace Tests                        #
# (Cannot re-violate before expiration of current violation #
#  or while in grace period after most recent expiration)   #
#############################################################
@pytest.mark.django_db(transaction=True)
def test_reviolation_while_in_violation_single_policy(short_low_unset_policy, target1):
    """
    Test whether a new Violation is made after violating a Policy while already being in violation
    (Basically can a target violate a policy when an unexpired violation of that same Policy exists)
    """
    # start bad behavior
    runtime = create_violation(target1, short_low_unset_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([short_low_unset_policy])

    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=short_low_unset_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, short_low_unset_policy)
    time.sleep(runtime / 2)
    arbiter.eval.evaluate([short_low_unset_policy])

    # make sure no new violations were added for target with that policy
    assert not target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(runtime / 2)


@pytest.mark.django_db(transaction=True)
def test_violation_in_grace_single_policy(grace_no_lookback_policy, target1):
    """
    Test whether a new Violation is made after violating a Policy while in the grace period after a violation
    (Can a target violate a policy when in the grace period after the an expiration of a violation of that same Policy exists)
    """
    # start bad behavior
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([grace_no_lookback_policy])
    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=grace_no_lookback_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(grace_no_lookback_policy.penalty_duration.total_seconds())
    arbiter.eval.evaluate([grace_no_lookback_policy])

    # make sure no new violations were added for target with that policy
    assert not target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(max(runtime - grace_no_lookback_policy.grace_period.total_seconds(), 1))


@pytest.mark.django_db(transaction=True)
def test_violation_after_grace_single_policy(grace_no_lookback_policy, target1):
    """
    Test whether a new Violation is made after violating a Policy while past the grace period after a violation
    (Can a target violate a policy when not in the grace period after the an expiration of a violation of that same Policy exists)
    """
    # start bad behavior
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([grace_no_lookback_policy])
    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=grace_no_lookback_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # sleep until violation expires
    time.sleep(grace_no_lookback_policy.penalty_duration.total_seconds())
    arbiter.eval.evaluate([grace_no_lookback_policy])

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(grace_no_lookback_policy.grace_period.total_seconds())
    arbiter.eval.evaluate([grace_no_lookback_policy])

    # make sure a new violations was added for target with that policy
    assert target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(max(runtime - grace_no_lookback_policy.grace_period.total_seconds(), 1))


@pytest.mark.django_db(transaction=True)
def test_violation_in_grace_multiple_policy(
    grace_no_lookback_policy, short_low_soft_policy, target1
):
    """
    Test that when in grace for one Policy, another Policy can still be violated
    """
    # initialize querysets (not evaluated here)
    target_violations = Violation.objects.filter(
        target__unit=target1.unit, target__host=target1.host
    )
    target_grace_policy_violations = target_violations.filter(
        policy=grace_no_lookback_policy
    )
    target_soft_policy_violations = target_violations.filter(
        policy=short_low_soft_policy
    )

    # start bad behavior
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([grace_no_lookback_policy])

    first_violation = target_grace_policy_violations.first()
    assert first_violation != None

    # sleep until violation expires
    time.sleep(grace_no_lookback_policy.penalty_duration.total_seconds())
    arbiter.eval.evaluate([grace_no_lookback_policy])

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(grace_no_lookback_policy.grace_period.total_seconds() - 2)
    arbiter.eval.evaluate([grace_no_lookback_policy, short_low_soft_policy])

    # make sure no new violations for policy in grace, but new violation for other policy not in grace
    assert not target_grace_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()
    assert target_soft_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(
        max(
            runtime - (grace_no_lookback_policy.grace_period.total_seconds() - 2),
            1,
        )
    )


@pytest.mark.django_db(transaction=True)
def test_violation_in_grace_single_policy_multiple_targets(
    grace_no_lookback_policy, target1, target2
):
    """
    Test whether one target being in grace for Policy, blocks another target from violating that Policy
    """
    # start bad behavior
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([grace_no_lookback_policy])
    target1_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=grace_no_lookback_policy,
    )
    first_violation = target1_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior for traget1 and start it for target2
    runtime = create_violation(target1, grace_no_lookback_policy)
    runtime = create_violation(target2, grace_no_lookback_policy)
    time.sleep(grace_no_lookback_policy.penalty_duration.total_seconds() + 2)
    arbiter.eval.evaluate([grace_no_lookback_policy])

    # make sure no new violations were added for target the original target, but one was for the second target
    target2_policy_violations = Violation.objects.filter(
        target__unit=target2.unit,
        target__host=target2.host,
        policy=grace_no_lookback_policy,
    )
    assert not target1_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()
    assert target2_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(max(runtime - grace_no_lookback_policy.grace_period.total_seconds(), 1))


#############################################################
#                  Duration Scaling Tests                   #
# (The expiration of violations should grow based on number #
#  of previous violations and the lookback window size)     #
#############################################################
@pytest.mark.django_db(transaction=True)
def test_repeat_violation_scales(long_lookback_no_grace_policy, target1):
    """
    Test that the duration of a violation directl after a previous violation expires, it larger (scales)
    """
    # start bad behavior
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([long_lookback_no_grace_policy])
    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=long_lookback_no_grace_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    time.sleep(long_lookback_no_grace_policy.penalty_duration.total_seconds())
    arbiter.eval.evaluate([long_lookback_no_grace_policy])

    # make sure a new violation was added for target with that policy
    second_violation = target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).first()
    assert second_violation != None

    assert second_violation.duration > first_violation.duration
    assert second_violation.offense_count == 2

    time.sleep(
        max(
            runtime - long_lookback_no_grace_policy.penalty_duration.total_seconds(),
            1,
        )
    )


@pytest.mark.django_db(transaction=True)
def test_repeat_violation_scales_multiple_targets(
    long_lookback_no_grace_policy, target1, target2
):
    """
    Test that one target's violation cannot scale another target's duration for their violation on the same policy, but they scale independently
    """
    # init querysets (not evaluated yet)
    target1_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=long_lookback_no_grace_policy,
    )
    target2_policy_violations = Violation.objects.filter(
        target__unit=target2.unit,
        target__host=target2.host,
        policy=long_lookback_no_grace_policy,
    )

    # start bad behavior
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([long_lookback_no_grace_policy])

    first_violation_target1 = target1_policy_violations.first()
    assert first_violation_target1 != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    runtime = create_violation(target2, long_lookback_no_grace_policy)
    time.sleep(long_lookback_no_grace_policy.penalty_duration.total_seconds() + 1)
    arbiter.eval.evaluate([long_lookback_no_grace_policy])

    # make sure a new violation was added for target with that policy
    second_violation_target1 = target1_policy_violations.filter(
        timestamp__gt=first_violation_target1.timestamp
    ).first()
    first_violation_target2 = target2_policy_violations.filter(
        timestamp__gt=first_violation_target1.timestamp
    ).first()
    assert second_violation_target1 != None
    assert first_violation_target2 != None

    assert second_violation_target1.duration > first_violation_target1.duration
    assert second_violation_target1.offense_count == 2

    assert second_violation_target1.duration > first_violation_target2.duration
    assert first_violation_target2.offense_count == 1

    # cleanup and wait for process to end
    time.sleep(
        max(
            runtime - long_lookback_no_grace_policy.penalty_duration.total_seconds(),
            1,
        )
    )


@pytest.mark.django_db(transaction=True)
def test_repeat_violation_scales_multiple_policy(
    long_lookback_no_grace_policy, short_lookback_no_grace_policy, target1
):
    """
    Test that the if a target has a violation on two policies, that violating one does not scale the other, but they scale independently
    """
    # start bad behavior
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([long_lookback_no_grace_policy])

    target_long_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=long_lookback_no_grace_policy,
    )
    target_short_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=short_lookback_no_grace_policy,
    )

    first_violation = target_long_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    time.sleep(long_lookback_no_grace_policy.penalty_duration.total_seconds())
    arbiter.eval.evaluate(
        [long_lookback_no_grace_policy, short_lookback_no_grace_policy]
    )

    # make sure a new violation was added for target with that policy
    second_violation = target_long_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).first()
    first_short_violation = target_short_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).first()
    assert second_violation != None
    assert first_short_violation != None

    assert second_violation.duration > first_violation.duration
    assert second_violation.offense_count == 2
    assert first_short_violation.offense_count == 1

    time.sleep(
        max(
            runtime - long_lookback_no_grace_policy.penalty_duration.total_seconds(),
            1,
        )
    )


@pytest.mark.django_db(transaction=True)
def test_short_lookback_forgets_old_violations(short_lookback_no_grace_policy, target1):
    """
    Test that when an old violation's time leaves the lookback window, the policy 'forgets' it and no longer scales the next violation with it
    """
    # start bad behavior
    runtime = create_violation(target1, short_lookback_no_grace_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([short_lookback_no_grace_policy])
    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=short_lookback_no_grace_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, short_lookback_no_grace_policy)
    time.sleep(short_lookback_no_grace_policy.penalty_duration.total_seconds() + 1)
    arbiter.eval.evaluate([short_lookback_no_grace_policy])

    # make sure a new violation was added for target with that policy
    second_violation = target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).first()
    assert second_violation != None

    assert second_violation.duration > first_violation.duration
    assert second_violation.offense_count == 2

    # wait til near the end of current violation then continue bad behavior a third time
    time.sleep(second_violation.duration.total_seconds() - runtime)
    runtime = create_violation(target1, short_lookback_no_grace_policy)
    time.sleep(runtime)

    arbiter.eval.evaluate([short_lookback_no_grace_policy])

    # make sure a new violation was added for target with that policy
    third_violation = target_policy_violations.filter(
        timestamp__gt=second_violation.timestamp
    ).first()
    assert third_violation != None

    # should be greater duration than first, but still offense 2 because policy forgot first offense
    assert third_violation.offense_count == 2
    assert third_violation.duration > first_violation.duration


@pytest.mark.django_db(transaction=True)
def test_lookback_and_grace(long_lookback_with_grace_policy, target1):
    """
    Test that a policy with grace and lookback/scaling works properly
    """
    # start bad behavior
    runtime = create_violation(target1, long_lookback_with_grace_policy)
    time.sleep(runtime)

    # eval and make sure first violation applied then grab it
    arbiter.eval.evaluate([long_lookback_with_grace_policy])
    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=long_lookback_with_grace_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, long_lookback_with_grace_policy)
    time.sleep(long_lookback_with_grace_policy.penalty_duration.total_seconds())
    arbiter.eval.evaluate([long_lookback_with_grace_policy])

    # make sure no new violations were added for target with that policy
    assert not target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # wait til grace is over then continue bad behavior
    time.sleep(long_lookback_with_grace_policy.grace_period.total_seconds())
    runtime = create_violation(target1, long_lookback_with_grace_policy)
    time.sleep(runtime)

    # make sure a new violation was added for target with that policy
    arbiter.eval.evaluate([long_lookback_with_grace_policy])
    second_violation = target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).first()
    assert second_violation != None

    assert second_violation.duration > first_violation.duration
    assert second_violation.offense_count == 2


# TODO: test unit whitelist and process whitelist
