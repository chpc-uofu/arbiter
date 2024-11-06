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


def view_dashboard(request):
        agents = []
        try:
            result = PROMETHEUS_CONNECTION.custom_query('up{job=~"cgroup-warden.*"} > 0')
            agents = [strip_port(metric["metric"]["instance"]) for metric in result]
        except Exception as e:
            LOGGER.error(f"Could not query prometheus for cgroup-agent instances: {e}")

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
            return HttpResponse("Username is required.")
        if not (host := request.POST.get("host")):
            return HttpResponse("Host is required.")
        
        target = Target.objects.filter(username=username, host=host).first()
        if not target:
            return HttpResponse(f"No Target with name {username} on {host} found.")
        
        if not (prop := request.POST.get("prop")):
            return HttpResponse("Property is required.")
        if not (value := request.POST.get("value")):
            return HttpResponse("Value is required")
        
        try:
            v = float(value)
        except ValueError:
            return HttpResponse(f"Invalid value {value}")  
        
        if prop == "CPUQuotaPerSecUSec":
            v = cores_to_usec(v) if v != -1 else v
            limit = Limit.cpu_quota(v)
        elif prop == "MemoryMax":
            v = gib_to_bytes(v) if v != -1 else v
            limit = Limit.memory_max(v)
        else:
            return HttpResponse(f"Invalid property '{prop}'")

        status, message = asyncio.run(apply_single_limit(target, limit))
        if status == http.HTTPStatus.OK:
            current = [l for l in target.last_applied if l.name != limit.name]
            if limit.value != -1:
                current.append(limit)
            target.set_limits(current)
            target.save()
                
        return HttpResponse(f'{message}')


@permission_required('arbiter.execute_commands')
def clean(request):
    if request.method == "POST":
        if not (before := request.POST.get("before", "").strip()):
            return HttpResponse("Before is required for cleaning.")
        try:
            call_command('clean', before=before)
        except CommandError as e:
            return HttpResponse(f'Could not run clean: {e}')
        return HttpResponse("Ran clean successfully.")


@permission_required('arbiter.execute_commands')
def evaluate(request):
    if request.method == "POST":
        try:
            call_command('evaluate')
        except CommandError as e:
            return HttpResponse(f'Could not run clean: {e}')
    return HttpResponse("Ran evaluate successfully.")