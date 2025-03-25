import time
import pytest
import logging

from arbiter3.arbiter.eval import evaluate
from arbiter3.arbiter.models import Target, Violation

from testing.util import create_violation, duration


logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.WARNING)


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
    evaluate([short_low_harsh_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None  # here

    # make sure correct limits were applied
    should_be = short_low_harsh_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait out violation and make sure limits were removed
    time.sleep(duration(short_low_harsh_policy))
    evaluate([short_low_harsh_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
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
    evaluate([short_low_harsh_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait out violation
    waiting = max(duration(short_low_harsh_policy),
                  duration(short_low_medium_policy))
    time.sleep(waiting)

    # eval and make sure limits were removed
    evaluate([short_low_harsh_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
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
    evaluate([short_low_harsh_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(
        unit=target2.unit, host=target2.host).first()
    assert db_target1 != None
    assert db_target2 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be
    assert db_target2.limits == should_be

    # now wait out violation and re-evaluate
    time.sleep(duration(short_low_harsh_policy))
    evaluate([short_low_harsh_policy])

    # make sure limits got removed
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(
        unit=target2.unit, host=target2.host).first()
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
    evaluate([short_low_harsh_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(
        unit=target2.unit, host=target2.host).first()
    assert db_target1 != None
    assert db_target2 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be
    assert db_target2.limits == should_be

    # now wait out violation and re-evaluate
    time.sleep(max(duration(short_low_harsh_policy),
               duration(short_low_medium_policy)))
    evaluate([short_low_harsh_policy, short_low_medium_policy])

    # make sure limits got removed
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(
        unit=target2.unit, host=target2.host).first()
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
    evaluate([short_low_harsh_policy, short_mid_soft_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None

    # make sure correct limits were set
    should_be = short_low_harsh_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait out harsh violation and re-evaluate
    time.sleep(duration(short_low_harsh_policy))
    evaluate([short_low_harsh_policy, short_mid_soft_policy])

    # penalty for violation of soft policy has a longer duration, so it is still active
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    should_be = short_mid_soft_policy.penalty_constraints['tiers'][0]
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
    evaluate([short_low_unset_policy])

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
    evaluate([short_low_unset_policy])

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
    evaluate([grace_no_lookback_policy])
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
    evaluate([grace_no_lookback_policy])

    # make sure no new violations were added for target with that policy
    assert not target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(
        max(runtime - grace_no_lookback_policy.grace_period.total_seconds(), 1))


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
    evaluate([grace_no_lookback_policy])
    target_policy_violations = Violation.objects.filter(
        target__unit=target1.unit,
        target__host=target1.host,
        policy=grace_no_lookback_policy,
    )
    first_violation = target_policy_violations.first()
    assert first_violation != None

    # sleep until violation expires
    time.sleep(grace_no_lookback_policy.penalty_duration.total_seconds())
    evaluate([grace_no_lookback_policy])

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(grace_no_lookback_policy.grace_period.total_seconds())
    evaluate([grace_no_lookback_policy])

    # make sure a new violations was added for target with that policy
    assert target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # cleanup and make sure process ends
    time.sleep(
        max(runtime - grace_no_lookback_policy.grace_period.total_seconds(), 1))


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
    evaluate([grace_no_lookback_policy])

    first_violation = target_grace_policy_violations.first()
    assert first_violation != None

    # sleep until violation expires
    time.sleep(grace_no_lookback_policy.penalty_duration.total_seconds())
    evaluate([grace_no_lookback_policy])

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, grace_no_lookback_policy)
    time.sleep(grace_no_lookback_policy.grace_period.total_seconds() - 2)
    evaluate([grace_no_lookback_policy, short_low_soft_policy])

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
            runtime -
            (grace_no_lookback_policy.grace_period.total_seconds() - 2),
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
    evaluate([grace_no_lookback_policy])
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
    evaluate([grace_no_lookback_policy])

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
    time.sleep(
        max(runtime - grace_no_lookback_policy.grace_period.total_seconds(), 1))


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
    evaluate([long_lookback_no_grace_policy])
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
    evaluate([long_lookback_no_grace_policy])

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
    evaluate([long_lookback_no_grace_policy])

    first_violation_target1 = target1_policy_violations.first()
    assert first_violation_target1 != None

    # now continue bad behavior and see if new violation was made
    runtime = create_violation(target1, long_lookback_no_grace_policy)
    runtime = create_violation(target2, long_lookback_no_grace_policy)
    time.sleep(long_lookback_no_grace_policy.penalty_duration.total_seconds() + 1)
    evaluate([long_lookback_no_grace_policy])

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
    evaluate([long_lookback_no_grace_policy])

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
    evaluate(
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
    evaluate([short_lookback_no_grace_policy])
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
    evaluate([short_lookback_no_grace_policy])

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

    evaluate([short_lookback_no_grace_policy])

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
    evaluate([long_lookback_with_grace_policy])
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
    evaluate([long_lookback_with_grace_policy])

    # make sure no new violations were added for target with that policy
    assert not target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).exists()

    # wait til grace is over then continue bad behavior
    time.sleep(long_lookback_with_grace_policy.grace_period.total_seconds())
    runtime = create_violation(target1, long_lookback_with_grace_policy)
    time.sleep(runtime)

    # make sure a new violation was added for target with that policy
    evaluate([long_lookback_with_grace_policy])
    second_violation = target_policy_violations.filter(
        timestamp__gt=first_violation.timestamp
    ).first()
    assert second_violation != None

    assert second_violation.duration > first_violation.duration
    assert second_violation.offense_count == 2



####################################################
#               Base Policy Tests                  #
# (Base policy violation should be triggered on    #
#  login and harshest violation should still rule) #
####################################################
@pytest.mark.django_db(transaction=True)
def test_base_policy(base_soft_policy, target1):
    # start simple login
    runtime = create_violation(target1, base_soft_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([base_soft_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None 

    #get the violation and make sure there is no expiration
    viol = Violation.objects.filter(target=db_target1, policy=base_soft_policy).first()
    assert viol != None
    assert viol.expiration == None #doesnt expire
    assert viol.is_base_status 

    # make sure correct limits were applied
    should_be = base_soft_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait after login has ended and make sure limits are still present after new evaluate
    time.sleep(duration(base_soft_policy))
    evaluate([base_soft_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    assert db_target1.limits == should_be


@pytest.mark.django_db(transaction=True)
def test_base_overlap_policy(base_soft_policy, base_medium_policy, target1):
    # start simple login
    runtime = create_violation(target1, base_soft_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([base_soft_policy, base_medium_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None 

    #get the violation and make sure there is no expiration
    soft_viol = Violation.objects.filter(target=db_target1, policy=base_soft_policy).first()
    med_viol = Violation.objects.filter(target=db_target1, policy=base_medium_policy).first()
    assert soft_viol != None
    assert med_viol != None
    assert soft_viol.expiration == None #doesnt expire
    assert med_viol.expiration == None #doesnt expire
    assert soft_viol.is_base_status 
    assert med_viol.is_base_status 

    # make sure correct limits(harsher) were applied
    should_be = base_medium_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait after login has ended and make sure limits are still present after new evaluate
    time.sleep(duration(base_soft_policy))
    evaluate([base_soft_policy, base_medium_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    assert db_target1.limits == should_be


@pytest.mark.django_db(transaction=True)
def test_base_overlap_usage_policy(base_soft_policy, short_low_medium_policy, target1):
    # start bad behavior
    runtime = create_violation(target1, short_low_medium_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([base_soft_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None 

    #get the violation and make sure there is no expiration
    base_viol = Violation.objects.filter(target=db_target1, policy=base_soft_policy).first()
    assert base_viol != None
    assert base_viol.expiration == None #doesnt expire
    assert base_viol.is_base_status 

    # make sure correct limits(harsher) were applied
    should_be = short_low_medium_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait after login and ensure limits unset to the base status 
    time.sleep(duration(short_low_medium_policy))
    evaluate([base_soft_policy, short_low_medium_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    should_be = base_soft_policy.penalty_constraints['tiers'][0]
    assert db_target1 != None
    assert db_target1.limits == should_be


@pytest.mark.django_db(transaction=True)
def test_base_override_usage_policy(base_medium_policy, short_low_soft_policy, target1):
    """
    When a base policy is harsher than a usage policy violation, the base should win
    """
    # start bad behavior
    runtime = create_violation(target1, short_low_soft_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([base_medium_policy, short_low_soft_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None 

    #get the violation and make sure there is no expiration
    base_viol = Violation.objects.filter(target=db_target1, policy=base_medium_policy).first()
    assert base_viol != None
    assert base_viol.expiration == None #doesnt expire
    assert base_viol.is_base_status 

    # make sure correct limits(harsher) were applied
    should_be = base_medium_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait after login and ensure limits unset to the base status 
    time.sleep(duration(short_low_soft_policy))
    evaluate([base_medium_policy, short_low_soft_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    assert db_target1.limits == should_be


@pytest.mark.django_db(transaction=True)
def test_base_overlap_policy(base_soft_policy, base_medium_policy, target1):
    # start simple login
    runtime = create_violation(target1, base_soft_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([base_soft_policy, base_medium_policy])
    db_target1 = Target.objects.filter(
        unit=target1.unit, host=target1.host).first()
    assert db_target1 != None 

    #get the violation and make sure there is no expiration
    soft_viol = Violation.objects.filter(target=db_target1, policy=base_soft_policy).first()
    med_viol = Violation.objects.filter(target=db_target1, policy=base_medium_policy).first()
    assert soft_viol != None
    assert med_viol != None
    assert soft_viol.expiration == None #doesnt expire
    assert med_viol.expiration == None #doesnt expire
    assert soft_viol.is_base_status 
    assert med_viol.is_base_status 

    # make sure correct limits(harsher) were applied
    should_be = base_medium_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

    # now wait after login has ended and make sure limits are still present after new evaluate
    time.sleep(duration(base_soft_policy))
    evaluate([base_soft_policy, base_medium_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None
    assert db_target1.limits == should_be


########################################################
#               Whitelist Policy Tests                 #
# (Base/usage policy should exclude users on whitelist #
#  and usage should not trigger on whitelisted procs)  #
########################################################
@pytest.mark.django_db(transaction=True)
def test_base_whitelist_policy(base_userwhitelist_policy, target1, target2):
    # start simple login
    runtime = create_violation(target1, base_userwhitelist_policy)
    runtime = create_violation(target2, base_userwhitelist_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([base_userwhitelist_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target1 != None 
    assert db_target2 != None 

    # make sure target1 was excluded but target2 was not
    target1_viol = Violation.objects.filter(target=db_target1, policy=base_userwhitelist_policy).first()
    target2_viol = Violation.objects.filter(target=db_target2, policy=base_userwhitelist_policy).first()
    assert target1_viol == None
    assert target2_viol != None

    # make sure correct limits were applied
    should_be = base_userwhitelist_policy.penalty_constraints['tiers'][0]
    assert len(db_target1.limits) == 0
    assert db_target2.limits == should_be


@pytest.mark.django_db(transaction=True)
def test_usage_userwhitelist_policy(low_harsh_userwhitelist_policy, target1, target2):
    """
    here the policy ignores target1's username
    """
    # start bad behavior
    runtime = create_violation(target1, low_harsh_userwhitelist_policy)
    runtime = create_violation(target2, low_harsh_userwhitelist_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([low_harsh_userwhitelist_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target1 != None 
    assert db_target2 != None 

    # make sure target1 was excluded but target2 was not
    target1_viol = Violation.objects.filter(target=db_target1, policy=low_harsh_userwhitelist_policy).first()
    target2_viol = Violation.objects.filter(target=db_target2, policy=low_harsh_userwhitelist_policy).first()
    assert target1_viol == None
    assert target2_viol != None

    # make sure correct limits were applied
    should_be = low_harsh_userwhitelist_policy.penalty_constraints['tiers'][0]
    assert len(db_target1.limits) == 0
    assert db_target2.limits == should_be

     # now wait out violation and make sure limits were removed
    time.sleep(duration(low_harsh_userwhitelist_policy))
    evaluate([low_harsh_userwhitelist_policy])
    db_target2 = Target.objects.filter(unit=target2.unit, host=target2.host).first()
    assert db_target2 != None

    # make sure target has no limits applied
    assert len(db_target2.limits) == 0


@pytest.mark.django_db(transaction=True)
def test_usage_procwhitelist_policy(low_harsh_procwhitelist_policy, short_low_cpu_policy, target1):
    """
    here the policy ignores the proc stress-ng-cpu
    """
    # start bad behavior
    runtime = create_violation(target1, short_low_cpu_policy)
    time.sleep(runtime)

    # eval and make sure db target was created
    evaluate([low_harsh_procwhitelist_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None 

    # make sure cpu usage did not trigger violation
    cpu_viol = Violation.objects.filter(target=db_target1, policy=low_harsh_procwhitelist_policy).first()
    assert cpu_viol == None

    # make no limits were applied
    assert len(db_target1.limits) == 0

    # now make violation using memory
    runtime = create_violation(target1, low_harsh_procwhitelist_policy)
    time.sleep(runtime)
    evaluate([low_harsh_procwhitelist_policy])
    db_target1 = Target.objects.filter(unit=target1.unit, host=target1.host).first()
    assert db_target1 != None

    # make sure memory process actually caused violation 
    mem_viol = Violation.objects.filter(target=db_target1, policy=low_harsh_procwhitelist_policy).first()
    assert mem_viol != None

    should_be = low_harsh_procwhitelist_policy.penalty_constraints['tiers'][0]
    assert db_target1.limits == should_be

########################################################
#               Deactive Policy Tests                  #
# (deactivating/reactivating policies should update    #
#              limits accordingly)                     #
########################################################

########################################################
#               Tiered Policy Tests                    #
# (repeated violations should upgrade the penalty's    #
#         tier/limits accordingly)                     #
########################################################