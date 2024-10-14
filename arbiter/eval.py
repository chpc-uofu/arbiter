import functools
import http
import asyncio
import aiohttp
from django.utils import timezone
import logging
from arbiter.models import *
from arbiter.email import send_violation_email
from collections import defaultdict
from arbiter.utils import set_property, strip_port
from typing import TYPE_CHECKING
from arbiter.conf import (
    PROMETHEUS_CONNECTION,
    WARDEN_JOB,
    ARBITER_PERMISSIVE_MODE,
    ARBITER_NOTIFY_USERS,
    ARBITER_MIN_UID,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def query_violations(policies: list[Policy]) -> list[Violation]:
    """
    Queries prometheus for violations of each policy given, and returns
    a list of all violations.
    """
    violations = []
    for policy in policies:
        query = policy.query
        response = PROMETHEUS_CONNECTION.custom_query(query)
        for result in response:
            unit = result["metric"]["unit"]
            host = strip_port(result["metric"]["instance"])

            target, _ = Target.objects.get_or_create(unit=unit, host=host)

            if target.uid < ARBITER_MIN_UID:
                continue

            unit_violations = Violation.objects.filter(policy=policy, target=target)
            in_grace = unit_violations.filter(
                expiration__gte=timezone.now() - policy.grace_period
            ).exists()

            if not in_grace:
                num_offense = unit_violations.filter(
                    timestamp__gte=timezone.now() - policy.lookback_window
                ).count()
                expiration = timezone.now() + (
                    policy.penalty.duration
                    * (1 + policy.penalty.repeat_offense_scale * num_offense)
                )

                new_violation = Violation(
                    target=target,
                    policy=policy,
                    expiration=expiration,
                    offense_count=num_offense + 1,
                )
                violations.append(new_violation)

    return violations


def get_affected_hosts(domain) -> list[str]:
    """
    For a given domain, calculated all other hosts in the domain that
    the penalty for a violation in that domain would apply to.
    """
    up_query = f"up{{job=~'{WARDEN_JOB}', instance=~'{domain}'}}"
    result = PROMETHEUS_CONNECTION.custom_query(up_query)
    return [strip_port(r["metric"]["instance"]) for r in result]


async def apply_limits(
    limits: list[Limit],
    target: Target,
    session: aiohttp.ClientSession,
):
    """
    For a given target, attempt to apply a number of property limits on that target.
    """

    to_apply = {limit.property.name: limit for limit in limits}
    async for limit in target.last_applied.all():
        prop = limit.property.name

        if prop in to_apply and to_apply[prop].value == limit.value:
            to_apply.pop(prop)

        elif prop not in to_apply:
            unset = Limit(property=limit.property, value=Limit.UNSET_LIMIT)
            to_apply[prop] = unset

    applied = []
    for limit in to_apply.values():
        payload = limit.property_json()
        status, message = await set_property(target, session, payload)
        if status == http.HTTPStatus.OK:
            applied.append(limit)

    return (target, applied)


def reduce_limits(limits: list[Limit]) -> list[Limit]:
    """
    Takes a list of many possible limits of many properties,
    and reduces them to just one possible limit per property,
    depending on how they are compared.
    """

    limit_map = defaultdict(list)
    for limit in limits:
        limit_map[limit.property.name].append(limit)

    reduced = []
    for candidates in limit_map.values():
        reduced.append(functools.reduce(Limit.compare, candidates))

    return reduced


async def reduce_and_apply_limits(
    applicable: dict[Target, list[Limit]],
):
    """
    For each target with applicable limits, first reduce the list of limits (taking
    the 'harshest' limit defined by the property operator) and then apply those limits.
    """

    async with aiohttp.ClientSession() as session, asyncio.TaskGroup() as tg:
        tasks = []
        for target, limit_list in applicable.items():
            reduced = reduce_limits(limit_list)
            tasks.append(tg.create_task(apply_limits(reduced, target, session)))

    final_applications = {}
    for task in tasks:
        target, applications = task.result()
        final_applications[target] = applications

        if not applications:
            continue

        current = []
        for old in target.last_applied.all():
            if old.property.name not in [a.property.name for a in applications]:
                current.append(old)

        not_unset = [a for a in applications if a.value != Limit.UNSET_LIMIT]
        current.extend(not_unset)
        await target.last_applied.aset(current)
        await target.asave()

    return final_applications


def create_event_for_eval(violations):
    violations_json = []
    for violation in violations:
        violations_json.append(
            {
                "target": str(violation.target),
                "policy": str(violation.policy),
                "offense_count": violation.offense_count,
            }
        )

    Event.objects.create(
        type=Event.EventTypes.EVALUATION, data={"violations": violations_json}
    )


def evaluate(policies: "QuerySet[Policy]" = None):
    policies = policies or Policy.objects.all()

    violations = query_violations(policies)
    Violation.objects.bulk_create(violations, ignore_conflicts=True)

    unexpired = Violation.objects.filter(expiration__gt=timezone.now())
    unexpired = unexpired.prefetch_related("policy__penalty__limits__property")

    targets = Target.objects.prefetch_related("last_applied__property").all()
    affected_hosts = {
        policy.domain: get_affected_hosts(policy.domain) for policy in policies
    }
    applicable_limits = {target: [] for target in targets}
    for v in unexpired:
        for host in affected_hosts[v.policy.domain]:
            target, _ = targets.get_or_create(unit=v.target.unit, host=host)

            target.last_applied.prefetch_related("property")
            if target not in applicable_limits:
                applicable_limits[target] = []

            limits = v.policy.penalty.limits.all()
            applicable_limits[target].extend(limits)

    create_event_for_eval(violations)

    if ARBITER_NOTIFY_USERS:
        for violation in violations:
            send_violation_email(violation)

    if ARBITER_PERMISSIVE_MODE:
        return

    try:
        asyncio.run(reduce_and_apply_limits(applicable_limits))
    except Exception as e:
        logger.error(f"Error: {e}")
        return
