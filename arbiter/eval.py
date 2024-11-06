import functools
import http
import asyncio
import aiohttp
import logging
import collections

from django.db.models import Q
from django.utils import timezone

from arbiter.utils import strip_port, get_uid
from arbiter.models import Target, Violation, Policy, Limit, Event
from arbiter.email import send_violation_emails
from arbiter.conf import (
    PROMETHEUS_CONNECTION,
    WARDEN_JOB,
    ARBITER_PERMISSIVE_MODE,
    ARBITER_NOTIFY_USERS,
    ARBITER_MIN_UID,
    WARDEN_DISABLE_AUTH,
    WARDEN_DISABLE_SSL,
    WARDEN_DISABLE_TLS,
    WARDEN_PORT,
    WARDEN_BEARER,
)

logger = logging.getLogger(__name__)


async def set_property(target: Target, session: aiohttp.ClientSession, limit: Limit) -> tuple[http.HTTPStatus, str]:
    if WARDEN_DISABLE_TLS:
        endpoint = f"http://{target.host}:{WARDEN_PORT}/control"
    else:
        endpoint = f"https://{target.host}:{WARDEN_PORT}/control"

    payload = {"unit": target.unit, "property": limit.json()}

    if WARDEN_DISABLE_AUTH:
        auth_header = None
    else:
        auth_header = {"Authorization": "Bearer " + WARDEN_BEARER}
    try:
        async with session.post(
            url=endpoint,
            json=payload,
            timeout=5,
            headers=auth_header,
            ssl=WARDEN_DISABLE_SSL,
        ) as response:
            status = response.status
            message = await response.text()
        
    except Exception as e:
        status = http.HTTPStatus.SERVICE_UNAVAILABLE
        message = f"Service Unavailable : {e}"

    return status, message


def create_violation(target: Target, policy: Policy) -> Violation:
    unit_violations = Violation.objects.filter(policy=policy, target=target)

    if policy.is_base_policy:
        if unit_violations.exists():
            return None
        return Violation(
            target=target,
            policy=policy,
            expiration=None,
            offense_count=None,
            is_base_status=True,
        )

    in_grace = unit_violations.filter(
        expiration__gte=timezone.now() - policy.grace_period
    ).exists()

    if not in_grace:
        num_offense = unit_violations.filter(
            timestamp__gte=timezone.now() - policy.repeated_offense_lookback
        ).count()
        expiration = timezone.now() + policy.penalty_duration * (
            1 + policy.repeated_offense_scalar * num_offense
        )
        offense_count = num_offense + 1
        return Violation(
            target=target,
            policy=policy,
            expiration=expiration,
            offense_count=offense_count,
        )

    return None


def query_violations(policies: list[Policy]) -> list[Violation]:
    violations = []
    for policy in policies:
        if not policy.active:
            continue
        
        response = PROMETHEUS_CONNECTION.custom_query(policy.query)
        for result in response:
            unit = result["metric"]["unit"]
            host = strip_port(result["metric"]["instance"])
            username = result["metric"]["username"]

            if get_uid(unit) < ARBITER_MIN_UID:
                continue

            target, created = Target.objects.get_or_create(
                unit=unit, host=host, username=username
            )
            if created:
                logger.info(f"new target {target}")

            if violation := create_violation(target, policy):
                violations.append(violation)
                logger.info(f"New violation of '{policy}' by '{target}'")

    return violations


def get_affected_hosts(domain) -> list[str]:
    """
    For a given domain, calculated all other hosts in the domain that
    the penalty for a violation in that domain would apply to.
    """
    up_query = f"up{{job=~'{WARDEN_JOB}', instance=~'{domain}'}}"
    result = PROMETHEUS_CONNECTION.custom_query(up_query)
    return [strip_port(r["metric"]["instance"]) for r in result]


async def apply_limits(limits: list[Limit], target: Target, session: aiohttp.ClientSession):
    """
    For a given target, attempt to apply a number of property limits on that target.
    """

    applied = []
    for limit in limits:
        status, message = await set_property(target, session, limit)
        if status == http.HTTPStatus.OK:
            logger.info(f"successfully applied limit {limit} to {target}")
            applied.append(limit)
        else:
            logger.warning(f"could not apply {limit} to {target}: {message}")

    return (target, applied)


def reduce_limits(limits: list[Limit]) -> list[Limit]:
    limit_map = collections.defaultdict(list)
    for limit in limits:
        limit_map[limit.name].append(limit)

    reduced = []
    for candidates in limit_map.values():
        compare = lambda a, b: a if a.value < b.value else b
        reduced.append(functools.reduce(compare, candidates))

    logger.info(f"REDUCED: {reduced}")
    return reduced


def resolve_limits(target: Target, limits: list[Limit]) -> list[Limit]:
    resolved = limits[:]
    for current in Limit.from_json(target.last_applied):
        if current in resolved:
            resolved.remove(current)
        elif current.name not in [r.name for r in resolved]:
            resolved.append(Limit(name=current.name, value=Limit.UNSET_LIMIT))

    return resolved


async def reduce_and_apply_limits(applicable: dict[Target, list[Limit]]):
    async with aiohttp.ClientSession() as session, asyncio.TaskGroup() as tg:
        tasks = []
        for target, limit_list in applicable.items():
            logger.info(f"APPLICABLE {limit_list}")
            reduced = reduce_limits(limit_list)
            resolved = resolve_limits(target, reduced)
            tasks.append(tg.create_task(apply_limits(resolved, target, session)))

    final_applications = {}
    for task in tasks:
        target, applications = task.result()
        final_applications[target] = applications
        if not applications:
            continue

        current = []
        for old in Limit.from_json(target.last_applied):
            if old.name not in [a.name for a in applications]:
                current.append(old)

        not_unset = [a for a in applications if a.value != Limit.UNSET_LIMIT]
        current.extend(not_unset)
        target.last_applied = Limit.to_json(*current)
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


def evaluate(policies=None):
    policies = policies or Policy.objects.all()

    violations = query_violations(policies)
    Violation.objects.bulk_create(violations, ignore_conflicts=True)

    unexpired = Violation.objects.filter(
        Q(expiration__gt=timezone.now()) | Q(expiration__isnull=True)
    )
    unexpired = unexpired.prefetch_related("policy")

    targets = Target.objects.all()
    affected_hosts = {
        policy.domain: get_affected_hosts(policy.domain) for policy in policies
    }
    applicable_limits = {target: [] for target in targets}
    for v in unexpired:
        for host in affected_hosts[v.policy.domain]:
            target, _ = targets.get_or_create(
                unit=v.target.unit, host=host, username=v.target.username
            )

            if target not in applicable_limits:
                applicable_limits[target] = []

            limits = Limit.from_json(v.policy.penalty_constraints)
            applicable_limits[target].extend(limits)

    create_event_for_eval(violations)

    if not ARBITER_NOTIFY_USERS:
        send_violation_emails(violations)

    if ARBITER_PERMISSIVE_MODE:
        return

    try:
        asyncio.run(reduce_and_apply_limits(applicable_limits))
    except ExceptionGroup as eg:
        for e in eg.exceptions:
            logger.error(f"Error: {e} ")
        
