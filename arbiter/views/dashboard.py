import logging
import asyncio
import aiohttp
import http

from django.shortcuts import render
from django.core.management import call_command
from django.http import HttpResponse
from django.core.management.base import CommandError
from django.contrib.auth.decorators import permission_required

from arbiter.conf import PROMETHEUS_CONNECTION
from arbiter.utils import strip_port, cores_to_usec, gib_to_bytes
from arbiter.models import Violation, Event, Limit, Target
from arbiter.eval import set_property

from .nav import navbar

LOGGER = logging.getLogger(__name__)


def message_http(message:str, status:str = "success"):
    return HttpResponse(f'<li class="{status}">{message}</li>')

def view_dashboard(request):
    agents = []
    try:
        result = PROMETHEUS_CONNECTION.custom_query('up{job=~"cgroup-warden.*"} > 0')
        agents = [strip_port(metric["metric"]["instance"]) for metric in result]
    except Exception as e:
        LOGGER.error(f"Could not query promethues for cgroup-agent instances: {e}")

    last_eval = Event.objects.order_by("timestamp").last()

    context = dict(
        title="Arbiter Dashboard",
        violations=Violation.objects.all().order_by("-timestamp")[:10],
        agents=agents,
        limits=[Limit.cpu_quota(-1), Limit.memory_max(-1)],
        last_evaluated=last_eval.timestamp if last_eval else "Never",
        navbar=navbar(request)
    )

    return render(request, "arbiter/dashboard.html", context)

@permission_required('arbiter.execute_commands')
def apply(request):
    
    async def apply_single_limit(target: Target, limit: Limit):
        async with aiohttp.ClientSession() as session:
            return await set_property(target, session, limit)

    if request.method == "POST":
        if not (username := request.POST.get("username")):
            return message_http("Username is required.",'error')
        if not (host := request.POST.get("host")):
            return message_http("Host is required.",'error')
        
        target = Target.objects.filter(username=username, host=host).first()
        if not target:
            return message_http(f"No Target with name {username} on {host} found.",'error')
        
        if not (prop := request.POST.get("prop")):
            return message_http("Property is required.",'error')
        if not (value := request.POST.get("value")):
            return message_http("Value is required",'error')
        
        try:
            v = float(value)
        except ValueError:
            return message_http(f'Invalid value {value}','error')  
        
        if prop == "CPUQuotaPerSecUSec":
            v = cores_to_usec(v) if v != -1 else v
            limit = Limit.cpu_quota(v)
        elif prop == "MemoryMax":
            v = gib_to_bytes(v) if v != -1 else v
            limit = Limit.memory_max(v)
        else:
            return message_http(f'Invalid property "{prop}"', 'error')

        status, message = asyncio.run(apply_single_limit(target, limit))
        status_str = "error"
        if status == http.HTTPStatus.OK:
            status_str = "success"
            current = [l for l in target.last_applied if l.name != limit.name]
            if limit.value != -1:
                current.append(limit)
            target.set_limits(current)
            target.save()
            
        return message_http(f'{message}', status_str)


@permission_required('arbiter.execute_commands')
def clean(request):
    if request.method == "POST":
        if not (before := request.POST.get("before", "").strip()):
            return message_http("Before is required for cleaning.", 'error')
        try:
            call_command('clean', before=before)
        except CommandError as e:
            return message_http(f'Could not run clean: {e}', 'error')
        return message_http("Ran clean successfully.")


@permission_required('arbiter.execute_commands')
def evaluate(request):
    if request.method == "POST":
        try:
            call_command('evaluate')
        except CommandError as e:
            return message_http(f'Could not run clean: {e}', 'error')
    return message_http("Ran evaluate successfully.")