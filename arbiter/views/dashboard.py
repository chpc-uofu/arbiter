import logging

from django.shortcuts import render
from django.core.management import call_command
from django.http import HttpResponse

from arbiter.conf import PROMETHEUS_CONNECTION
from arbiter.utils import strip_port
from arbiter.models import Violation, Event, Limit

from .nav import navbar

LOGGER = logging.getLogger(__name__)


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


def run_command(command, *args, **options) -> str:
    try:
        call_command(command, *args, **options)
        return f"Ran '{command}' successfully!"
    except Exception as e:
        return f"Could not execute command {command}: {e}"


def dashboard_command(request, command):
    
    if not request.user.has_perm("arbiter.change_dashboard"):
        error = "You do not have permission to execute commands"
        return render(request, "arbiter/message.html", {"error": error})

    match command:
        case "evaluate":
            message = run_command(command)
        case "clean":
            if not (before := request.POST.get("before")):
                message = "Please provide a time to clean violations before."
            else:
                message = run_command(command, before=before.strip())
        case "apply":
            message = "Applied limit successfully"
        case _:
            message = f"Invalid command '{command}'"
        
    return HttpResponse(message)
    