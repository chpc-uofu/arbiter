from datetime import datetime

from django.shortcuts import render
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponse

import arbiter.plots as plots
from arbiter.models import Violation


def make_aware(time: datetime | None) -> datetime | None:
    if not time:
        return None
    else:
        return timezone.make_aware(timezone.datetime.fromisoformat(time))


def validate_request_parameters(request) -> dict:
    if not request.user.has_perm("arbiter.change_dashboard"):
        raise PermissionError("You do not hav permission to view usage graphs")
    
    end = make_aware(request.GET.get("end-time")) or timezone.now()
    start = make_aware(request.GET.get("start-time")) or end - timezone.timedelta(minutes=10)
    if start >= end:
        raise ValueError("Given start time is after given end time")
    
    step = request.GET.get("step-value", "30") + request.GET.get("step-unit", "s")
    step = plots.align_with_prom_limit(start, end, step)

    host = request.GET.get("host")
    if not host:
        raise ValueError("Hostname is required")
    
    username = request.GET.get("username")

    return dict(start=start, end=end, step=step, host=host, username=username)


def user_proc_cpu_graph(request):
    try:
        request_parameters = validate_request_parameters(request)
    except (PermissionError, ValueError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    
    figure = plots.cpu_usage_figures(
        host = request_parameters["host"],
        start = request_parameters["start"],
        end = request_parameters['end'],
        step = request_parameters['step'],
        username = request_parameters["username"]
    )
    
    context = dict()
    if figure:
        context["graph"] = mark_safe(figure.to_html(default_width="100%", default_height="400px"))
    else:
        context["error"] = 'unable to generate graph'

    return render(request, "arbiter/graph.html", context=context)
    

def user_proc_memory_graph(request):
    try:
        request_parameters = validate_request_parameters(request)
    except (PermissionError, ValueError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    
    figure = plots.mem_usage_figures(
        host = request_parameters["host"],
        start = request_parameters["start"],
        end = request_parameters['end'],
        step = request_parameters['step'],
        username = request_parameters["username"]
    )
    
    context = dict()
    if figure:
        context["graph"] = mark_safe(figure.to_html(default_width="100%", default_height="400px"))
    else:
        context["error"] = 'unable to generate graph'

    return render(request, "arbiter/graph.html", context=context)


def violation_usage(request, violation_id, usage_type):

    context = dict()

    if not request.user.has_perm("arbiter.change_dashboard"):
        context["warning"] = "You do not have permission to view usage graphs"
        return render(request, "arbiter/graph.html", context=context)

    violation = Violation.objects.filter(pk=violation_id).first()
    if not violation:
        context["error"] = "Violation not found"
        return render(request, "arbiter/graph.html", context=context)

    step = request.GET.get("step-value", "30") + request.GET.get("step-unit", "s")

    figures = plots.violation_usage_figures(violation, usage_type, step)

    if figures:
        context["graph"] = mark_safe(figures.chart.to_html(default_width="100%", default_height="400px"))
        context["pie"] = mark_safe(figures.pie.to_html(default_width="100%", default_height="400px"))
    else:
        context["warning"] = "unable to generate usage graphs"

    return render(request, "arbiter/graph.html", context=context)


def violation_cpu_usage(request, violation_id):
    return violation_usage(request, violation_id, plots.CPU_USAGE)


def violation_memory_usage(request, violation_id):
    return violation_usage(request, violation_id, plots.MEM_USAGE)


def apply_property_for_user(request):
    return render(request, "arbiter/message.html")


def violation_metrics_scrape(request):
    unexpired_violations_metrics = (
        Violation.objects.filter(expiration__gte=timezone.now())
        .values("policy__name", "offense_count")
        .annotate(count=Count("*"))
    )

    metric_name = "arbiter_violations_count"

    exported_str = f"""# HELP {metric_name} The count of the current unexpired violations under that policy/offense count\n# TYPE {metric_name} gauge\n"""

    for metric in unexpired_violations_metrics:
        policy_name = metric["policy__name"]
        offense_count = metric["offense_count"]
        violation_count = metric["count"]
        exported_str += f'{metric_name}{{policy="{policy_name}", offense_count="{offense_count}"}} {violation_count}'

    return HttpResponse(exported_str, content_type="text")
