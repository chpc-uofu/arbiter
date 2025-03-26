import http
import asyncio
import aiohttp
import logging
import re

from django.db.models import Q
from django.utils import timezone

from prometheus_api_client import PrometheusApiClientException

from arbiter3.arbiter.utils import split_port, get_uid
from arbiter3.arbiter.models import Target, Violation, Policy, Limits, Event, UNSET_LIMIT, CPU_QUOTA, MEMORY_MAX
from arbiter3.arbiter.email import send_violation_email
from arbiter3.arbiter.conf import (
    PROMETHEUS_CONNECTION,
    WARDEN_JOB,
    ARBITER_PERMISSIVE_MODE,
    ARBITER_MIN_UID,
    WARDEN_VERIFY_SSL,
    WARDEN_USE_TLS,
    WARDEN_BEARER,
    WARDEN_RUNTIME,
)

logger = logging.getLogger(__name__)

def refresh_limits():
    refresh_limits_cpu()
    refresh_limits_mem()
    

def refresh_limits_cpu():
    return refresh_limit(limit_query="cgroup_warden_cpu_quota", limit_name="CPUQuotaPerSecUSec")


def refresh_limits_mem():
    return refresh_limit(limit_query="cgroup_warden_memory_max", limit_name="MemoryMax")


def refresh_limit(limit_query: str, limit_name: str) -> list[Target]:
    invalid_targets = []

    try: 
        response = PROMETHEUS_CONNECTION.query(limit_query)
    except PrometheusApiClientException as e:
        logger.error(f"Unable to assert limits set: {e}")

    for result in response:
        cgroup = result.metric['cgroup']
        matches = re.findall(r"^/user.slice/(user-\d+.slice)$", cgroup)
        if len(matches) < 1:
            logger.warning(f"invalid cgroup: {cgroup}")
            continue
        unit = matches[0]
        host, port = split_port(result.metric["instance"])
        username = result.metric["username"]
        value = int(result.value.value)

        if get_uid(unit) < ARBITER_MIN_UID:
            continue

        target = Target.objects.filter(host=host, username=username).first()
        if not target:
            continue

        expected = target.limits.get(limit_name, -1) 
        if expected != value:
            logger.warning(f"targets limits to not match actual: expected {expected}, actual: {value}")
            target.limits[limit_name] = value
            target.save()

    return invalid_targets


async def set_property(target: Target, session: aiohttp.ClientSession, name: str, value: any) -> tuple[http.HTTPStatus, str]:
    if WARDEN_USE_TLS:
        endpoint = f"https://{target.endpoint}/control"
    else:
        endpoint = f"http://{target.endpoint}/control"

    payload = {"unit": target.unit, "property": {'name': name, 'value': value}, "runtime": WARDEN_RUNTIME}

    if WARDEN_BEARER:
        auth_header = {"Authorization": "Bearer " + WARDEN_BEARER}
    else:
        auth_header = None
    try:
        async with session.post(
            url=endpoint,
            json=payload,
            timeout=5,
            headers=auth_header,
            ssl=WARDEN_VERIFY_SSL,
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
        expiration__gte=timezone.now() - policy.grace_period).exists()

    if not in_grace:
        num_offense = unit_violations.filter(
            timestamp__gte=timezone.now() - policy.repeated_offense_lookback).count()
        expiration = timezone.now() + policy.penalty_duration * \
            (1 + policy.repeated_offense_scalar * num_offense)
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

        try:
            response = PROMETHEUS_CONNECTION.query(policy.query)
        except PrometheusApiClientException as e:
            logger.error(f"Unable to query violations: {e}")
            return violations

        for result in response:
            cgroup = result.metric['cgroup']
            matches = re.findall(r"^/user.slice/(user-\d+.slice)$", cgroup)
            if len(matches) < 1:
                logger.warning(f"invalid cgroup: {cgroup}")
                continue
            unit = matches[0]
            host, port = split_port(result.metric["instance"])
            username = result.metric["username"]

            if get_uid(unit) < ARBITER_MIN_UID:
                continue

            target, created = Target.objects.update_or_create(
                host=host, username=username, defaults=dict(port=port, unit=unit))
            if created:
                logger.info(f"new target {target}")

            if violation := create_violation(target, policy):
                violations.append(violation)
                logger.info(f"New violation of '{policy}' by '{target}'")

    return violations


async def apply_limits(limits: Limits, target: Target, session: aiohttp.ClientSession) -> tuple[Target, Limits]:
    applied: Limits = {}
    for name, value in limits.items():
        status, message = await set_property(target, session, name, value)
        if status == http.HTTPStatus.OK:
            logger.info(
                f"successfully applied limit {name} = {value} to {target}")
            applied[name] = value
        else:
            logger.warning(
                f"could not apply {name} = {value} to {target}: {message}")

    return target, applied


def reduce_limits(limits_list: list[Limits]) -> Limits:
    reduced: Limits = {}
    for limits in limits_list:
        for name, value in limits.items():
            if name not in reduced:
                reduced[name] = value
            elif value < reduced[name]:
                reduced[name] = value

    return reduced


def resolve_limits(target: Target, limits: Limits) -> Limits:
    resolved = {name: value for name, value in limits.items()}

    for name, value in target.limits.items():
        if name not in limits:
            resolved[name] = UNSET_LIMIT
        elif limits[name] == value:
            del resolved[name]

    return resolved


async def reduce_and_apply_limits(applicable: dict[Target, list[Limits]]):
    async with aiohttp.ClientSession() as session, asyncio.TaskGroup() as tg:
        tasks = []
        for target, limits_list in applicable.items():
            reduced: Limits = reduce_limits(limits_list)
            resolved: Limits = resolve_limits(target, reduced)
            tasks.append(tg.create_task(
                apply_limits(resolved, target, session)))

    final_applications = {}
    for task in tasks:
        target, applications = task.result()
        final_applications[target] = applications
        if not applications:
            continue
        target.update_limits(applications)
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
    policies = [p for p in policies if p.active]

    violations = query_violations(policies)
    Violation.objects.bulk_create(violations, ignore_conflicts=True)


    unexpired = Violation.objects.filter(Q(expiration__gt=timezone.now()) | Q(expiration__isnull=True), policy__active=True)
    unexpired = unexpired.prefetch_related("policy")

    targets = Target.objects.all()
    applicable_limits = {target: [] for target in targets}
    for v in unexpired:
        for host, port in v.policy.affected_hosts:
            target, _ = targets.update_or_create(
                host=host, username=v.target.username, defaults=dict(port=port, unit=v.target.unit))

            if target not in applicable_limits:
                applicable_limits[target] = []

            applicable_limits[target].append(v.limits)

    create_event_for_eval(violations)

    for violation in violations:
        if not violation.is_base_status:
            message = send_violation_email(violation)
            logger.info(message)

    if ARBITER_PERMISSIVE_MODE:
        return

    try:
        asyncio.run(reduce_and_apply_limits(applicable_limits))
    except ExceptionGroup as eg:
        for e in eg.exceptions:
            logger.error(f"{e} ")

    # assert_cpu_limits_set()
