from datetime import datetime

from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils import timezone

import arbiter3.arbiter.plots as plots
from arbiter3.arbiter.models import Violation


class InvalidRequest(Exception):
    pass


def create_graph(request, figure_func):
    if not request.user.has_perm("arbiter.arbiter_view"):
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
    is_proc = request.GET.get('username', '') != ''
    try:
        figure = create_graph(request, plots.cpu_usage_figure)
    except (PermissionError, InvalidRequest, plots.QueryError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    return render_figure(figure, request, include_other_note=is_proc)


def user_proc_memory_graph(request):
    is_proc = request.GET.get('username', '') != ''
    try:
        figure = create_graph(request, plots.mem_usage_figure)
    except (PermissionError, InvalidRequest, plots.QueryError) as e:
        return render(request, "arbiter/graph.html", context=dict(error=e))
    return render_figure(figure, request, include_other_note=is_proc)


def create_graph_violation(request, figure_func, violation_id):
    if not request.user.has_perm("arbiter.arbiter_view"):
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


def make_aware(time: datetime | None) -> datetime | None:
    if not time:
        return None
    else:
        return timezone.make_aware(timezone.datetime.fromisoformat(time))


def render_figure(figure, request, include_other_note: bool = False):
    context = dict()
    if figure:
        theme = request.GET.get("theme", "light")
        template = "plotly_dark" if theme == "dark" else "plotly_white"

        figure.update_layout(template=template)

        context['other_note'] = include_other_note
        context["graph"] = mark_safe(figure.to_html(
            default_width="100%", default_height="400px"))
    else:
        context["error"] = 'unable to generate graph'

    return render(request, "arbiter/graph.html", context=context)
