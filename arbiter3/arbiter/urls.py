from django.urls import path, include
from django.contrib import admin
from arbiter3.arbiter.views import base_policy, graphs, usage_policy, violation, dashboard, index, user, metrics

app_name = "arbiter"

urlpatterns = [
    path("policy/base/add/", base_policy.new_base_policy, name="new-base-policy"),
    path("policy/base/", base_policy.BasePolicyListView.as_view(),
         name="list-base-policy"),
    path("policy/base/<int:policy_id>",
         base_policy.change_base_policy, name="change-base-policy"),

    path("policy/usage/add/", usage_policy.new_usage_policy,
         name="new-usage-policy"),
    path("policy/usage/", usage_policy.UsagePolicyListView.as_view(),
         name="list-usage-policy"),
    path("policy/usage/<int:policy_id>",usage_policy.change_usage_policy, name="change-usage-policy"),

    path("violation/", violation.ViolationListView.as_view(), name="list-violation"),
    path("violation/<int:violation_id>",
         violation.change_violation, name="change-violation"),
    path("user/<str:username>", user.get_user_breakdown, name="user-breakdown"),
    path("user/lookup/", user.get_user_lookup, name="user-lookup"),

    path("", index.view_index, name="view-index"),
    path("dashboard", dashboard.view_dashboard, name="view-dashboard"),
    path("clean", dashboard.clean, name="clean"),
    #path("apply", dashboard.apply, name="apply"),
    path("evaluate", dashboard.evaluate, name="evaluate"),

    path("graphs/proc/cpu", graphs.user_proc_cpu_graph,
         name="user-proc-cpu-graph"),
    path("graphs/proc/memory", graphs.user_proc_memory_graph,
         name="user-proc-memory-graph"),

    path("graphs/proc/cpu/<int:violation_id>",
         graphs.violation_cpu_usage, name="violation-proc-cpu-graph"),
    path("graphs/proc/memory/<int:violation_id>",
         graphs.violation_memory_usage, name="violation-proc-memory-graph"),

    path("metrics", metrics.violation_metrics_scrape, name="violation_metric_scrape"),
]
