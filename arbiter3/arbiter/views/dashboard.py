import logging
import asyncio
import aiohttp
import http

from django.shortcuts import render
from django.core.management import call_command
from django.http import HttpResponse
from django.core.management.base import CommandError
from django.contrib.auth.decorators import permission_required
from django.contrib import messages

from arbiter3.arbiter.conf import PROMETHEUS_CONNECTION, WARDEN_JOB
from arbiter3.arbiter.utils import split_port, cores_to_usec, gib_to_bytes
from arbiter3.arbiter.models import Violation, Event, Target
from arbiter3.arbiter.eval import set_property
from arbiter3.arbiter.prop import CPU_QUOTA, MEMORY_MAX, MEMORY_SWAP_MAX

from .nav import navbar

LOGGER = logging.getLogger(__name__)


def message_http(message: str, status: str = "success"):
    return HttpResponse(f'<li class="{status}">{message}</li>')


@permission_required('arbiter.arbiter_view')
def view_dashboard(request):
    agents = []
    try:
        result = PROMETHEUS_CONNECTION.query(f'up{{job="{WARDEN_JOB}"}} == 1', timeout=3)
        agents = [r.metric['instance'] for r in result]
    except Exception as e:
        messages.warning(request, "Warning: Unable to connect to prometheus instance to query cgroup-warden instances")
        LOGGER.error(
            f"Could not query prometheus for cgroup-warden instances: {e}")

    last_eval = Event.objects.order_by("timestamp").last()

    prop_list = {"CPU Quota (cores)": CPU_QUOTA,
                 "Memory Quota (GiB)": MEMORY_MAX,
                 #"Memory Swap Quota (GiB)" : MEMORY_SWAP_MAX
                 }

    context = dict(
        title="Dashboard",
        violations=Violation.objects.filter(is_base_status=False).order_by("-timestamp")[:10],
        agents=agents,
        limits=prop_list,
        last_evaluated=last_eval.timestamp if last_eval else "Never",
        navbar=navbar(request)
    )

    return render(request, "arbiter/dashboard.html", context)

def apply(request):
    can_run = request.user.has_perm("arbiter.arbiter_administrator")
    if not can_run: 
        return message_http("You do not have permissions to apply limits", status="error")

    async def apply_single_property(target: Target, name, value):
        async with aiohttp.ClientSession() as session:
            return await set_property(target, session, name, value)

    if request.method == "POST":
        if not (username := request.POST.get("username")):
            return message_http("Username is required.", 'error')
        if not (instance := request.POST.get("apply-host")):
            return message_http("Host is required.", 'error')

        host, port = split_port(instance)

        target, created = Target.objects.update_or_create(
            host=host, username=username, defaults=dict(port=port))
        if not (prop := request.POST.get("prop")):
            return message_http("Property is required.", 'error')
        if not (value := request.POST.get("value")):
            return message_http("Value is required", 'error')

        try:
            v = float(value)
        except ValueError:
            return message_http(f'Invalid value {value}', 'error')

        if prop == CPU_QUOTA:
            v = cores_to_usec(v) if v != -1 else v
        elif prop == MEMORY_MAX or prop == MEMORY_SWAP_MAX:
            v = gib_to_bytes(v) if v != -1 else v
        else:
            return message_http(f'Invalid property "{prop}"', 'error')

        status, message = asyncio.run(apply_single_property(target, prop, v))
        if status == http.HTTPStatus.OK:
            target.update_limit(prop, v)
            target.save()
            if created:
                return message_http(f"Applied property for new target {username} on {host}.")
            return message_http(f"Applied property for target {username} on {host}.")

        return message_http(f'Unable to apply property: {message}', 'error')


def clean(request):
    can_run = request.user.has_perm("arbiter.arbiter_administrator")
    if not can_run: 
        return message_http("You do not have permissions to run commands", status="error")

    if request.method == "POST":
        if not (before := request.POST.get("before", "").strip()):
            return message_http("Before is required for cleaning.", 'error')
        try:
            call_command('clean', before=before)
        except CommandError as e:
            return message_http(f'Could not run clean: {e}', 'error')
        return message_http("Ran clean successfully.")


def evaluate(request):
    can_run = request.user.has_perm("arbiter.arbiter_administrator")
    if not can_run: 
        return message_http("You do not have permissions to run commands", status="error")
    
    if request.method == "POST":
        try:
            call_command('evaluate')
        except CommandError as e:
            return message_http(f'Could not run clean: {e}', 'error')
    return message_http("Ran evaluate successfully.")


