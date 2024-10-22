from django.urls import path
from arbiter.views import base_policy, graphs, usage_policy, violation, dashboard

app_name = "arbiter" 

urlpatterns = [
    path("policy/base/add/", base_policy.new_base_policy, name="new-base-policy"),
    path("policy/base/", base_policy.BasePolicyListView.as_view(), name="list-base-policy"),
    path("policy/base/<int:policy_id>", base_policy.change_base_policy, name="change-base-policy"),

    path("policy/usage/add/", usage_policy.new_usage_policy, name="new-usage-policy"),
    path("policy/usage/", usage_policy.UsagePolicyListView.as_view(), name="list-usage-policy"),
    path("policy/usage/<int:policy_id>", usage_policy.change_usage_policy, name="change-usage-policy"),
    
    path("violation/", violation.ViolationListView.as_view(), name="list-violation"),
    path("violation/<int:violation_id>", violation.change_violation, name="change-violation"),

    path("dashboard/", dashboard.view_dashboard, name="view-dashboard"),
    path("dashboard/clean", dashboard.clean, name="clean"),
    path("dashboard/apply", dashboard.apply, name="apply"),
    path("dashboard/evaluate", dashboard.evaluate, name="evaluate"),

    path("graphs/proc/cpu", graphs.user_proc_cpu_graph, name="user-proc-cpu-graph"),
    path("graphs/proc/memory",graphs.user_proc_memory_graph, name="user-proc-memory-graph"),

    path("graphs/violation/<int:violation_id>/cpu", graphs.violation_cpu_usage, name="user-violation-cpu-graph"),
    path("graphs/violation/<int:violation_id>/memory", graphs.violation_memory_usage, name="user-violation-memory-graph"),
    
    path("metrics", graphs.violation_metrics_scrape, name="violation_metric_scrape"),
]
