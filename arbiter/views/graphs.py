from django.shortcuts import render
from arbiter.models import  Violation
from django.db.models import Count
from django.utils.safestring import mark_safe
import arbiter.plots as plots
from django.utils import timezone
from django.http import HttpResponse
from arbiter.plots import Figures

def user_proc_graph(request, usage_type):
    if not request.user.has_perm("arbiter.change_dashboard"):
        return render(
            request,
            "arbiter/graph.html",
            context={"warning": "You do not have permission to view usage graphs"},
        )

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
        return render(
            request,
            "arbiter/graph.html",
            context={"error": "Given start time is after given end time"},
        )

    messages = {}
    aligned_step = plots.align_with_prom_limit(start_time, end_time, step)

    if aligned_step != step:
        message = f"Step size exceeded Promtheus's limit of {plots.PROMETHUS_POINT_LIMIT} points, so was aligned to {aligned_step}"
        messages["warning"] = message
        step = aligned_step
    username = request.GET.get("username", ".*")
    host = request.GET.get("host", ".*")
    if len(username) == 0:
        username = ".*"
    if host == "all":
        host = ".*"

    if usage_type == plots.CPU_USAGE:
        figures = plots.cpu_usage_figures(
            username_re=username,
            host_re=host,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )
    elif usage_type == plots.MEM_USAGE:
        figures = plots.mem_usage_figures(
            username_re=username,
            host_re=host,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )
    
    if not figures:
        return render(
            request,
            "arbiter/graph.html",
            context={
                "error": "Unable to form graphs (check that Prometheus is up or that usage is nonempty)"
            }
        )
    else:
        fig, pie = figures

    return render(
        request,
        "arbiter/graph.html",
        context={
            "graph": mark_safe(
                fig.to_html(default_width="100%", default_height="400px")
            ),
            "pie": mark_safe(pie.to_html(default_width="100%", default_height="400px")),
            **messages,
        },
    )


def user_proc_cpu_graph(request):
    return user_proc_graph(request, plots.CPU_USAGE)


def user_proc_memory_graph(request):
    return user_proc_graph(request, plots.MEM_USAGE)


def violation_usage(request, violation_id, usage_type):
    if not request.user.has_perm("arbiter.change_dashboard"):
        return render(
            request,
            "arbiter/graph.html",
            context={"warning": "You do not have permission to view usage graphs"},
        )

    violation = Violation.objects.filter(pk=violation_id).first()
    if not violation:
        return render(
            request,
            "arbiter/graph.html",
            context={"error": "Violation not found"},
        )

    step = request.GET.get("step-value", "30") + request.GET.get("step-unit", "s")

    graph, pie = plots.violation_usage_figures(violation, usage_type, step)

    messages = {}

    return render(
        request,
        "arbiter/graph.html",
        context={
            "graph": mark_safe(
                graph.to_html(default_width="100%", default_height="400px",  include_plotlyjs=False)
            ),
            "pie": mark_safe(pie.to_html(default_width="100%", default_height="400px",  include_plotlyjs=False)),
            **messages,
        },
    )


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
