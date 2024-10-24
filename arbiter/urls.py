from django.urls import path
from arbiter.views import policy, graphs

app_name = "arbiter"

urlpatterns = [
    path("policy/base/add/", policy.new_base_policy, name="new-base-policy"),
    path("policy/base/", policy.BasePolicyListView.as_view(), name="list-base-policy"),
    path("policy/base/<int:id>", policy.change_base_policy, name="change-base-policy"),
    path("policy/usage/add/", policy.new_usage_policy, name="new-usage-policy"),
    path(
        "policy/usage/", policy.UsagePolicyListView.as_view(), name="list-usage-policy"
    ),
    path(
        "policy/usage/<int:id>", policy.change_usage_policy, name="change-usage-policy"
    ),
    path("policy/<int:id>/convert-query", graphs.convert_policy, name="convert_policy"),
    path("graphs/proc/cpu", graphs.user_proc_cpu_graph, name="user-proc-cpu-graph"),
    path(
        "graphs/proc/memory",
        graphs.user_proc_memory_graph,
        name="user-proc-memory-graph",
    ),
    path(
        "graphs/violation/<int:violation_id>/cpu",
        graphs.violation_cpu_usage,
        name="user-violation-cpu-graph",
    ),
    path(
        "graphs/violation/<int:violation_id>/memory",
        graphs.violation_memory_usage,
        name="user-violation-memory-graph",
    ),
    path("apply-property", graphs.apply_property_for_user, name="apply-property"),
    path(
        "violation/<int:violation_id>/expire",
        graphs.expire_violation,
        name="expire-violation",
    ),
    path(
        "dashboard/command/<str:command>",
        graphs.dashboard_command,
        name="dashboard-command",
    ),
    path("metrics", graphs.violation_metrics_scrape, name="violation_metric_scrape"),
]
