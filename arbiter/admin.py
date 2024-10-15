from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.shortcuts import resolve_url
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django import forms
from django.urls import reverse
from django.db.models import Model
from logging import getLogger
from arbiter.utils import strip_port
from arbiter.conf import PROMETHEUS_CONNECTION
from arbiter import models

LOGGER = getLogger(__name__)


@admin.register(models.Violation)
class ViolationsAdmin(admin.ModelAdmin):
    list_display = [
        "target",
        "policy_link",
        "penalty_link",
        "expiration",
        "status",
    ]
    readonly_fields = ["plot_mem_usage", "plot_cpu_usage"]
    actions = ["expire_violation"]
    change_form_template = "arbiter/violation.html"

    @admin.display(description="Penalty", ordering="policy__penalty")
    def penalty_link(self, user_penalty: models.Violation):
        url = resolve_url(
            admin_urlname(models.Penalty._meta, "change"),
            user_penalty.policy.penalty.id,
        )
        return mark_safe(f'<a href="{url}">{user_penalty.policy.penalty}</a>')

    @admin.display(description="Policy", ordering="policy")
    def policy_link(self, user_penalty: models.Violation):
        url = resolve_url(
            admin_urlname(models.Policy._meta, "change"), user_penalty.policy.id
        )
        return mark_safe(f'<a href="{url}">{user_penalty.policy.name}</a>')

    @admin.display(description="Recorded Memory Usage")
    def plot_mem_usage(self, violation: models.Violation):
        if violation.pk is not None:
            return mark_safe(
                f"<div hx-get='{reverse('user-violation-memory-graph', kwargs={'violation_id':violation.id})}' hx-trigger='load' hx-target='this' hx-swap='innerHTML' hx-indicator='dots'></div>"
            )
        else:
            return "No data available"

    @admin.display(description="Recorded CPU Usage")
    def plot_cpu_usage(self, violation: models.Violation):
        if violation.pk is not None:
            return mark_safe(
                f"<div hx-get='{reverse('user-violation-cpu-graph', kwargs={'violation_id': violation.id})}' hx-trigger='load' hx-target='this' hx-swap='innerHTML' hx-indicator='dots'></div>"
            )
        else:
            return "No data available"

    @admin.display(description="Status")
    def status(self, violation: models.Violation):
        if violation.expired:
            return mark_safe(f"<em>Expired</em>")
        else:
            return mark_safe(f"<em>Active</em>")

    @admin.action(description="Expire Violation")
    def expire_violation(self, request: HttpRequest, violations):
        for violation in violations:
            if violation.expired:
                continue

            violation.expiration = timezone.now()
            violation.save()

    def has_change_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return True


@admin.register(models.Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ["name", "duration", "limits_list"]

    @admin.display(description="Limits", ordering="limits")
    def limits_list(self, penalty: models.Penalty):
        result = ""
        for limit in penalty.limits.all():
            url = resolve_url(
                admin_urlname(models.Property._meta, "change"),
                limit.property.id,
            )
            result += (
                f'<li><a href="{url}">{limit.property.name}</a>: {limit.value}</li>'
            )
        return mark_safe(f"<ul>{result}</ul>")


@admin.register(models.Limit)
class LimitAdmin(admin.ModelAdmin):
    list_display = ["id", "property_link", "value"]

    @admin.display(description="Property", ordering="property")
    def property_link(self, limit: models.Limit):
        url = resolve_url(
            admin_urlname(models.Property._meta, "change"),
            limit.property.id,
        )
        return mark_safe(f'<a href="{url}">{limit.property.name}</a>')


@admin.register(models.Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "operation"]


@admin.register(models.Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ["name", "penalty_link", "display_description", "domain", "is_base_policy"]
    change_form_template = "arbiter/policy.html"
    add_form_template = "arbiter/add_policy.html"
    
    @admin.display(description="Penalty", ordering="policy__penalty__name")
    def penalty_link(self, policy: models.Policy):
        url = resolve_url(
            admin_urlname(models.Penalty._meta, "change"),
            policy.penalty.id,
        )
        return mark_safe(
            f'<a href="{url}" title="{str(policy.penalty)}">{policy.penalty.name}</a>'
        )

    @admin.display(description="Description")
    def display_description(self, policy: models.Policy):
        if policy.description:
            return policy.description
        else:
            if policy.is_raw_query:
                return mark_safe(f"<dfn title='{policy.query}'>Raw Query</dfn>")
            else:
                return mark_safe(
                    f"<li>CPU Threshold: {policy.query_params.get('cpu_threshold')} cores</li> <br>\
                      <li>Memory Threshold: {policy.query_params.get('memory_threshold')} GiB</li> <br> \
                      <li>Time Window:  {policy.timewindow}</li>"
                )

    class BuilderForm(forms.ModelForm):
        class Meta:
            model = models.Policy
            exclude = ["query_params", "query"]

        cpu_threshold = forms.FloatField(
            label="CPU-usage Threshold",
            help_text="Usage threshold in cores for if someone is in violation",
        )
        memory_threshold = forms.FloatField(
            label="Memory-usage Thresold",
            help_text="Usage threshold in GiB for if someone is in violation",
        )

        process_whitelist = forms.CharField(
            max_length=1000,
            help_text="A regular expression for any process names you want to be excluded from a user's reported usage",
            required=False,
        )
        unit_whitelist = forms.CharField(
            max_length=1000,
            help_text="A regular expression for the units you don't want to this policy to apply to",
            required=False,
        )

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

            if self.instance.pk:
                query_params = self.instance.query_params

                self.fields["cpu_threshold"].initial = query_params.get(
                    "cpu_threshold", 100_000
                )
                self.fields["memory_threshold"].initial = query_params.get(
                    "memory_threshold", 100_000
                )
                self.fields["domain"].initial = query_params.get("domain", ".*")
                self.fields["process_whitelist"].initial = query_params.get(
                    "process_whitelist", ""
                )
            else:
                self.fields["cpu_threshold"].initial = 1.0
                self.fields["memory_threshold"].initial = 1.0

        def save(self, commit: bool = ...) -> Any:
            instance = super().save(False)

            instance.query_params = dict()
            instance.query_params["cpu_threshold"] = self.cleaned_data.get(
                "cpu_threshold", 1.0
            )
            instance.query_params["memory_threshold"] = self.cleaned_data.get(
                "memory_threshold", 1.0
            )
            instance.query_params["domain"] = self.cleaned_data.get("domain", ".*")

            if "process_whitelist" in self.cleaned_data:
                instance.query_params["process_whitelist"] = self.cleaned_data[
                    "process_whitelist"
                ]

            if commit:
                instance.save()

            return instance

    class RawForm(forms.ModelForm):
        class Meta:
            model = models.Policy
            exclude = ["query"]

        query = forms.CharField(
            max_length=1000,
            help_text="The raw (promQL) query for which every user returned is considered in violation",
            widget=forms.Textarea,
        )

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

            self.fields["query_params"].widget = self.fields[
                "query_params"
            ].hidden_widget()
            self.fields["query_params"].required = False

            if self.instance.pk:
                query_params = self.instance.query_params

                self.fields["query"].initial = query_params.get("raw", "")

        def save(self, commit: bool = ...) -> Any:
            instance = super().save(False)

            instance.query_params = dict()
            instance.query_params["raw"] = self.cleaned_data.get("query", "")

            if commit:
                instance.save()

            return instance
        
    class BaseForm(forms.ModelForm):
        class Meta:
            model = models.Policy
            fields = ['name', 'domain', 'description', 'penalty']
            
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

        def save(self, commit: bool = ...) -> Any:
            instance = super().save(False)
            return instance


    def get_form(
        self,
        request: Any,
        obj: Any | None = ...,
        change: bool = ...,
        **kwargs: Any,
    ) -> Any:
        if request.GET.get("base_policy") in ["True", "true", "yes", "t", "y"]:
            return PolicyAdmin.BaseForm
        if not obj:
            return PolicyAdmin.BuilderForm
        if obj.is_base_policy:
            return PolicyAdmin.BaseForm
        if obj.is_raw_query:
            return PolicyAdmin.RawForm
        else:
            return PolicyAdmin.BuilderForm
        
    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = ...,
        form_url: str = ...,
        extra_context: dict[str, bool] | None = ...,
    ) -> Any:

        extra_context = extra_context or dict()
        if object_id is not None:
            extra_context["raw"] = models.Policy.objects.get(id=object_id).is_raw_query
        if request.GET.get("base_policy") in ["True", "true", "yes", "t", "y"]:
            extra_context["base_policy"] = True

        return super().changeform_view(request, object_id, form_url, extra_context)


class DashboardAdmin(admin.ModelAdmin):
    # TODO:
    # - Put clean violations in violations list
    # - Add an Arbiters "Most Wanted" leaderboard for the most frequent violators
    # - Graph Arbiter actions?

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


class TargetAdmin(admin.ModelAdmin):
    list_display = ["username", "host"]
    list_filter = ["host"]
    search_fields = ["username", "host"]


admin.site.register(models.Target, TargetAdmin)
