"""
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
"""