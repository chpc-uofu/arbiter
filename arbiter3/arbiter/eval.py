import http
import asyncio
import aiohttp
import logging
import re
import json

from django.db.models import Q
from django.utils import timezone

from prometheus_api_client import PrometheusApiClientException

from arbiter3.arbiter.utils import split_port, get_uid
from arbiter3.arbiter.models import Target, Violation, Policy, Limits, Event, UNSET_LIMIT
from arbiter3.arbiter.email import send_violation_email
from arbiter3.arbiter.prop import CPU_QUOTA, MEMORY_MAX
from arbiter3.arbiter.conf import (
    PROMETHEUS_CONNECTION,
    WARDEN_JOB,
    ARBITER_MIN_UID,
    WARDEN_VERIFY_SSL,
    WARDEN_USE_TLS,
    WARDEN_BEARER,
    WARDEN_RUNTIME,
)

logger = logging.getLogger(__name__)

def refresh_limits(policy: Policy):
    if policy.active and not policy.watcher_mode:
        refresh_limits_cpu(policy.domain)
        refresh_limits_mem(policy.domain)
    

def refresh_limits_cpu(domain):
    return refresh_limit(limit_query=f'cgroup_warden_cpu_quota{{instance=~"{domain}"}}', limit_name=CPU_QUOTA)


def refresh_limits_mem(domain):
    return refresh_limit(limit_query=f'cgroup_warden_memory_max{{instance=~"{domain}"}}', limit_name=MEMORY_MAX)


def refresh_limit(limit_query: str, limit_name: str) -> list[Target]:
    invalid_targets = []

    try: 
        response = PROMETHEUS_CONNECTION.query(limit_query)
    except Exception as e:
        logger.error(f"Unable to assert limits set: {e}")
        return []

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
            logger.warning(f"{target.username}@{target.host} {limit_name} is set to an unexpected value: expected {expected}, actual: {value}")
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
            timeout=10, # might need larger timeout, when MemMax is set systemd tries to swap excess memory to disk which takes forever
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
        except Exception as e:
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


async def _apply_and_verify_limit(target: Target, session : aiohttp.ClientSession, name : str, value: any):
        status, message = await set_property(target, session, name, value)
        if status == http.HTTPStatus.OK:
            try:
                response: dict = json.loads(message)
                if warning := response.get("warning"):
                    logger.warning(f"recieved warning from {target.host}: {warning}")
                
                if newLimit := response.get("property", {}).get("value"):
                    value = newLimit
                else:
                    logger.warning(f"malformed response : {response}")
                    return None, False
            except json.JSONDecodeError:
                logger.warning("failed to decode json from response, possibly older warden version")

            logger.info(f"successfully applied limit {name} = {value} to {target}")
            return value, True
        else:
            logger.warning(f"could not apply {name} = {value} to {target}: {message}")
            return None, False


async def apply_limits(limits: Limits, target: Target, session: aiohttp.ClientSession) -> tuple[Target, Limits]:
    applied: Limits = {} 

    for name, value in limits.items():
        applied_limit, successful = await _apply_and_verify_limit(target, session, name, value)

        if successful:
            applied[name] = applied_limit

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
            target, _ = targets.update_or_create(host=host, username=v.target.username, defaults=dict(port=port, unit=v.target.unit))

            if target not in applicable_limits:
                applicable_limits[target] = []

            if not v.policy.watcher_mode:
                applicable_limits[target].append(v.limits)

    create_event_for_eval(violations)

    for violation in violations:
        if not violation.is_base_status:
            message = send_violation_email(violation)
            logger.info(message)

    try:
        asyncio.run(reduce_and_apply_limits(applicable_limits))
    except ExceptionGroup as eg:
        for e in eg.exceptions:
            logger.error(f"{e} ")

    # assert_cpu_limits_set()
