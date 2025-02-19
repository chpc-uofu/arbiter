from datetime import datetime

from django.shortcuts import render
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponse

import arbiter3.arbiter.plots as plots
from arbiter3.arbiter.models import Violation


class InvalidRequest(Exception):
    pass


def create_graph(request, figure_func):
    if not request.user.has_perm("arbiter.change_dashboard"):
        raise PermissionError(
            "You do not have permission to view usage graphs")

    end = make_aware(request.GET.get("end-time")) or timezone.now()
    start = make_aware(request.GET.get("start-time")) or end - \
        timezone.timedelta(minutes=10)
    if start >= end:
        raise InvalidRequest("Given start time is after given end time")

    step_value = request.GET.get("step-value", "30")
    if not step_value.isdigit():
        raise InvalidRequest("step value must be a number")

    step = f'{step_value}{request.GET.get("step-unit", "s")}'
    step = plots.align_with_prom_limit(start, end, step)

    if not (host := request.GET.get("host")):
        raise InvalidRequest("Hostname is required")

    username = request.GET.get("username")

    return figure_func(host=host, start=start, end=end, step=step, username=username)


def user_proc_cpu_graph(request):
    try:
        figure = create_graph(request, plots.cpu_usage_figure)
    except (PermissionError, InvalidRequest, plots.QueryError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    return render_figure(figure, request)


def user_proc_memory_graph(request):
    try:
        figure = create_graph(request, plots.mem_usage_figure)
    except (PermissionError, InvalidRequest, plots.QueryError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    return render_figure(figure, request)


def create_graph_violation(request, figure_func, violation_id):
    if not request.user.has_perm("arbiter.change_dashboard"):
        raise PermissionError(
            "You do not have permission to view usage graphs")
    violation = Violation.objects.get(pk=violation_id)
    return figure_func(violation)


def violation_cpu_usage(request, violation_id):
    try:
        figure = create_graph_violation(
            request, plots.violation_cpu_usage_figure, violation_id)
    except (PermissionError, Violation.DoesNotExist, plots.QueryError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    return render_figure(figure, request)


def violation_memory_usage(request, violation_id):
    try:
        figure = create_graph_violation(
            request, plots.violation_mem_usage_figure, violation_id)
    except (PermissionError, Violation.DoesNotExist, plots.QueryError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    return render_figure(figure, request)


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


def make_aware(time: datetime | None) -> datetime | None:
    if not time:
        return None
    else:
        return timezone.make_aware(timezone.datetime.fromisoformat(time))


def render_figure(figure, request):
    context = dict()
    if figure:
        context["graph"] = mark_safe(figure.to_html(
            default_width="100%", default_height="400px"))
    else:
        context["error"] = 'unable to generate graph'

    return render(request, "arbiter/graph.html", context=context)
