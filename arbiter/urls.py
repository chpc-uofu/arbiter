from django.urls import path
from . import views

from arbiter._views import policy

app_name = "arbiter" 

urlpatterns = [
    path("policy/base/add/", policy.new_base_policy, name="new-base-policy"),
    path("policy/base/", policy.BasePolicyListView.as_view(), name="list-base-policy"),
    path("policy/base/<int:id>", policy.change_base_policy, name="change-base-policy"),

    path("policy/usage/add/", policy.new_usage_policy, name="new-usage-policy"),
    path("policy/usage/", policy.UsagePolicyListView.as_view(), name="list-usage-policy"),
    path("policy/usage/<int:id>", policy.change_usage_policy, name="change-usage-policy"),

    path("policy/<int:id>/convert-query", views.convert_policy, name="convert_policy"),
    path("graphs/proc/cpu", views.user_proc_cpu_graph, name="user-proc-cpu-graph"),
    path(
        "graphs/proc/memory",
        views.user_proc_memory_graph,
        name="user-proc-memory-graph",
    ),
    path(
        "graphs/violation/<int:violation_id>/cpu",
        views.violation_cpu_usage,
        name="user-violation-cpu-graph",
    ),
    path(
        "graphs/violation/<int:violation_id>/memory",
        views.violation_memory_usage,
        name="user-violation-memory-graph",
    ),
    path("apply-property", views.apply_property_for_user, name="apply-property"),
    path(
        "violation/<int:violation_id>/expire",
        views.expire_violation,
        name="expire-violation",
    ),
    path(
        "dashboard/command/<str:command>",
        views.dashboard_command,
        name="dashboard-command",
    ),
    path("metrics", views.violation_metrics_scrape, name="violation_metric_scrape"),
]
