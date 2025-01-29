from django.shortcuts import render
from arbiter.models import Violation
from django.db.models import Count
from django.utils.safestring import mark_safe
import arbiter.plots as plots
from django.utils import timezone
from django.http import HttpResponse


def user_proc_graph(request, usage_type):

    context = dict()

    if not request.user.has_perm("arbiter.change_dashboard"):
        context['warning'] = "You do not have permission to view usage graphs"
        return render(request, "arbiter/graph.html", context=context)

    start_time = request.GET.get("start-time")
    end_time = request.GET.get("end-time")
    step = request.GET.get("step-value", "30") + request.GET.get("step-unit", "s")

    if not end_time:
        end_time = timezone.now()
    else:
        end_time = timezone.make_aware(timezone.datetime.fromisoformat(end_time))

    if not start_time:
        start_time = end_time - timezone.timedelta(minutes=10)
    else:
        start_time = timezone.make_aware(timezone.datetime.fromisoformat(start_time))

    if start_time >= end_time:
        context["error"] = "Given start time is after given end time"
        return render(request,"arbiter/graph.html", context=context)

    aligned_step = plots._align_with_prom_limit(start_time, end_time, step)
    if aligned_step != step:
        context['warning'] = f"Step size exceeded Promtheus's limit of {plots.PROMETHUS_POINT_LIMIT} points, so was aligned to {aligned_step}"
        step = aligned_step

    username = request.GET.get("username", ".*")
    host = request.GET.get("host", ".*")
    if len(username) == 0:
        username = ".*"
    if host == "all":
        host = ".*"

    if usage_type == plots.CPU_USAGE:
        create_figures = plots.cpu_usage_figures
    elif usage_type == plots.MEM_USAGE:
        create_figures = plots.mem_usage_figures
    else:
        context["error"] = "Invalid graph type"
        return render(request,"arbiter/graph.html", context=context)

    figures = create_figures(
        username_re=username,
        host_re=host,
        start_time=start_time,
        end_time=end_time,
        step=step,
    )

    if figures:
        context["graph"] = mark_safe(figures.chart.to_html(default_width="100%", default_height="400px"))
        context["pie"] = mark_safe(figures.pie.to_html(default_width="100%", default_height="400px"))
    else:
        context["warning"] = "unable to generate usage graphs"

    return render(request, "arbiter/graph.html", context=context)


def user_proc_cpu_graph(request):
    return user_proc_graph(request, plots.CPU_USAGE)


def user_proc_memory_graph(request):
    return user_proc_graph(request, plots.MEM_USAGE)


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
