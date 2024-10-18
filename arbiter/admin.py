from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.template.response import TemplateResponse
from django.db.models import Model
from logging import getLogger
from arbiter.utils import strip_port
from arbiter.conf import PROMETHEUS_CONNECTION
from arbiter import models

LOGGER = getLogger(__name__)


@admin.register(models.Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "domain", "is_base_policy"]
 


class DashboardAdmin(admin.ModelAdmin):
    class Dashboard(Model):
        class Meta:
            managed = False
            verbose_name_plural = "dashboard"

    change_list_template = "arbiter/dashboard.html"

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, str] | None = None
    ) -> TemplateResponse:
        context = extra_context or {}

        agents = []
        try:
            result = PROMETHEUS_CONNECTION.custom_query(
                'up{job=~"cgroup-warden.*"} > 0'
            )
            agents = [strip_port(metric["metric"]["instance"]) for metric in result]
        except Exception as e:
            LOGGER.error(f"Could not query promethues for cgroup-agent instances: {e}")

        last_eval = models.Event.objects.order_by("timestamp").last()

        context.update(
            title="Arbiter Dashboard",
            violations=models.Violation.objects.all().order_by("-timestamp")[:10],
            agents=agents,
            last_evaluated=last_eval.timestamp if last_eval else "Never",
            properties=models.Property.objects.all(),
        )
        return super().changelist_view(request, context)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return DashboardAdmin.Dashboard.objects.none()

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False


admin.site.register(DashboardAdmin.Dashboard, DashboardAdmin)