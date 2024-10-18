from django.shortcuts import render
from arbiter.models import Policy, Violation 
from django.db.models import Count
from django.shortcuts import redirect
from django.contrib import messages
from django.core.management import call_command
from django.utils.safestring import mark_safe
import arbiter.plots as plots
from django.utils import timezone
import aiohttp
import asyncio
from django.http import HttpResponse
from arbiter.utils import set_property


def convert_policy(request, id: int):
    selected_policy = Policy.objects.filter(pk=id).first()

    if not selected_policy:
        messages.error(request, "Policy not found")
        return redirect(f"admin:arbiter_policy_changelist")

    match request.POST.get("action"):
        case "To Raw Query":
            if selected_policy.is_raw_query:
                messages.error(request, "Policy already uses a raw query")
                return redirect("admin:arbiter_policy_change", selected_policy.pk)

            selected_policy.query_params["raw"] = selected_policy.query
            selected_policy.save()

        case "To Builder Query":
            if not selected_policy.is_raw_query:
                messages.error(request, "Policy already uses a builder query")
                return redirect("admin:arbiter_policy_change", selected_policy.pk)
            selected_policy.query_params.pop("raw")
            selected_policy.query_params[
                "cpu_threshold"
            ] = selected_policy.query_params.get("cpu_threshold", 1.0)
            selected_policy.query_params[
                "memory_threshold"
            ] = selected_policy.query_params.get("memory_threshold", 1.0)
            selected_policy.query_params[
                "time_window"
            ] = selected_policy.query_params.get("time_window", "15m")
            selected_policy.save()
        case _:
            messages.error(request, "Action not recognized")
            return redirect("admin:arbiter_policy_change", selected_policy.pk)

    return redirect(f"admin:arbiter_policy_change", selected_policy.pk)


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
        fig, pie = plots.cpu_usage_figures(
            username_re=username,
            host_re=host,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )
    elif usage_type == plots.MEM_USAGE:
        fig, pie = plots.mem_usage_figures(
            username_re=username,
            host_re=host,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )

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
                graph.to_html(default_width="100%", default_height="400px")
            ),
            "pie": mark_safe(pie.to_html(default_width="100%", default_height="400px")),
            **messages,
        },
    )


def violation_cpu_usage(request, violation_id):
    return violation_usage(request, violation_id, plots.CPU_USAGE)


def violation_memory_usage(request, violation_id):
    return violation_usage(request, violation_id, plots.MEM_USAGE)


def apply_property_for_user(request):
    return render(request, "arbiter/message.html")


def dashboard_command(request, command):
    context = dict()
    args = dict()
    if not request.user.has_perm("arbiter.change_dashboard"):
        context["error"] = "You do not have permission to execute commands"
        return render(request, "arbiter/message.html", context)

    if command == "evaluate":
        message = f"Ran evaluation loop successfully. Check the logs for violations"

    elif command == "clean":
        if not request.POST.get("before", "").strip():
            context["error"] = "Please provide a time to clean violations before."
            return render(request, "arbiter/message.html", context)
        else:
            args["before"] = request.POST.get("before")

        message = f"Cleaned violation history successfully."

    else:
        message = f"Executed the command <dfn>{command}</dfn> successfully!"

    try:
        call_command(command, **args)
        context["info"] = mark_safe(message)
    except Exception as e:
        context["error"] = mark_safe(f"Could not execute command {command}: {e}")

    return render(request, "arbiter/message.html", context)


def expire_violation(request, violation_id):
    if not request.user.has_perm("arbiter.delete_violation"):
        messages.error(request, "You do not have permission to execute commands")
        return redirect("admin:arbiter_violation_changelist")

    violation = Violation.objects.filter(pk=violation_id).first()

    if not violation:
        messages.error(request, "Violation not found")
        return redirect("admin:arbiter_dashboard_changelist")

    if violation.expired:
        messages.warning(request, "Violation was already expired")
        return redirect("admin:arbiter_violation_changelist")

    violation.expiration = timezone.now()
    violation.save()
    messages.info(request, "Violation expired successfully")

    return redirect("admin:arbiter_violation_changelist")


def violation_metrics_scrape(request):
    # arbiter_violations{policy="foobar", offense_count=1} 2
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
