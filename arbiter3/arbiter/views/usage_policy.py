from django.forms.renderers import BaseRenderer
from django.shortcuts import render, redirect
from django import forms
from django.utils.safestring import mark_safe
from django.views.generic.list import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
import json
from dataclasses import dataclass

from arbiter3.arbiter.models import UsagePolicy, Limits, QueryData, QueryParameters, CPU_QUOTA, MEMORY_MAX
from arbiter3.arbiter.utils import usec_to_cores, bytes_to_gib, cores_to_usec, gib_to_bytes

from .nav import navbar


@dataclass
class ConstraintTier:
    memory_gib: float = None
    cpu_cores: float = None


class TieredPenaltyWidget(forms.Widget):
    template_name = "arbiter/penalty_widget.html"

    class Media:
        css = {
            "all": []
        }
        js = ['js/tiers-widget.js',]

    def get_context(self, name: str, value, attrs=None):
        context = super().get_context(name, value, attrs)
        if not value or value == 'null':
            constraints = {'tiers': []}
        else:
            constraints = json.loads(value)

        view_constraints = []
        if constraints == []:
            return context
        for tier_limits in constraints.get('tiers', []):
            tier = ConstraintTier()

            if mem_max := tier_limits.get(MEMORY_MAX):
                tier.memory_gib = bytes_to_gib(mem_max)

            if cpu_quota := tier_limits.get(CPU_QUOTA):
                tier.cpu_cores = usec_to_cores(cpu_quota)

            view_constraints.append(tier)

        context['tiers'] = view_constraints
        return context


class UsagePolicyListView(LoginRequiredMixin, ListView):
    model = UsagePolicy
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        context["can_create"] = self.request.user.has_perm(
            "arbiter.add_usagepolicy")
        context["title"] = "Usage Policies"
        return context


class UsagePolicyForm(forms.ModelForm):
    proc_whitelist = forms.CharField(
        label="Query Process Whitelist", required=False)
    user_whitelist = forms.CharField(
        label="Query User Whitelist", required=False)
    cpu_threshold = forms.FloatField(
        label="Query CPU Threshold", required=False)
    mem_threshold = forms.FloatField(
        label="Query Memory Threshold", required=False)

    class Meta:
        model = UsagePolicy
        fields = ["name", "domain", "description", "penalty_duration", "repeated_offense_scalar",
                  "grace_period", "repeated_offense_lookback", "lookback", "active", "penalty_constraints"]
        widgets = {'grace_period': forms.TimeInput(), "repeated_offense_lookback": forms.TimeInput(
        ), "penalty_constraints": TieredPenaltyWidget}

    def __init__(self, *args, disabled=False, **kwargs):
        super().__init__(*args, **kwargs)

        if query_data := self.instance.query_data:
            if cpu_threshold := query_data["params"]["cpu_threshold"]:
                self.fields['cpu_threshold'].initial = cpu_threshold
            if mem_threshold := query_data["params"]["mem_threshold"]:
                self.fields['mem_threshold'].initial = bytes_to_gib(
                    mem_threshold)
            self.fields['proc_whitelist'].initial = query_data["params"]["proc_whitelist"]
            self.fields['user_whitelist'].initial = query_data["params"]["user_whitelist"]

        if disabled:
            for field in self.fields.values():
                field.widget.attrs['disabled'] = True

    def clean_cpu_limit(self):
        if cpu := self.cleaned_data["cpu_limit"]:
            return cores_to_usec(cpu)
        return None

    def clean_mem_limit(self):
        if mem := self.cleaned_data["mem_limit"]:
            return gib_to_bytes(mem)
        return None

    def clean_penalty_constraints(self):
        if constraints := self.cleaned_data["penalty_constraints"]:
            converted_tiers = []
            for tier in constraints['tiers']:

                tier_penalty_status = {}
                if cpu_quota := tier.get('cpu_quota'):
                    tier_penalty_status[CPU_QUOTA] = cores_to_usec(cpu_quota)
                if memory_max := tier.get('memory_max'):
                    tier_penalty_status[MEMORY_MAX] = gib_to_bytes(memory_max)

                if tier_penalty_status:
                    converted_tiers.append(tier_penalty_status)

            converted_constraints = {'tiers': converted_tiers}
            return converted_constraints
        return {'tiers': []}

    def clean_cpu_threshold(self):
        if cpu := self.cleaned_data["cpu_threshold"]:
            return cpu
        return None

    def clean_mem_threshold(self):
        if mem := self.cleaned_data["mem_threshold"]:
            return gib_to_bytes(mem)
        return None

    def clean_user_whitelist(self):
        return self.cleaned_data["user_whitelist"] or None

    def clean_proc_whitelist(self):
        return self.cleaned_data["proc_whitelist"] or None

    def clean(self):
        cleaned_data = super().clean()

    def save(self, commit=True):
        policy = super().save(commit=False)
        policy.is_base_policy = True

        params = QueryParameters(
            cpu_threshold=self.cleaned_data["cpu_threshold"],
            mem_threshold=self.cleaned_data["mem_threshold"],
            user_whitelist=self.cleaned_data["user_whitelist"],
            proc_whitelist=self.cleaned_data["proc_whitelist"],
        )
        policy.query_data = QueryData.build_query(
            lookback=policy.lookback,
            domain=policy.domain,
            params=params
        ).json()

        policy.save()


@login_required(login_url=reverse_lazy("login"))
def new_usage_policy(request):
    can_change = request.user.has_perm("arbiter.add_usagepolicy")

    if not can_change:
        messages.error(
            request, "You do not have permissions to create a Usage Policy")
        return redirect("arbiter:view-dashboard")

    if request.method == "POST":
        form = UsagePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully created usage policy.")
            return redirect("arbiter:list-usage-policy")
    else:
        form = UsagePolicyForm()

    context = {"form": form, "navbar": navbar(
        request), "can_change": can_change, "title": "Create Usage Policy"}
    return render(request, "arbiter/change_view.html", context)


@login_required(login_url=reverse_lazy("login"))
def change_usage_policy(request, policy_id):
    policy = UsagePolicy.objects.filter(pk=policy_id).first()

    can_change = request.user.has_perm("arbiter.change_usagepolicy")

    if not policy:
        messages.error(request, "Usage Policy not found.")
        return redirect("arbiter:list-usage-policy")

    if request.method == "POST":
        if not can_change:
            messages.error(
                request, "You do not have permissions to change a Usage Policy")
            return redirect(request.path_info)

        form = UsagePolicyForm(request.POST, instance=policy)
        if "save" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Successfully changed usage policy.")
            return redirect("arbiter:list-usage-policy")
        if "delete" in request.POST:
            policy.delete()
            messages.success(request, "Successfully removed usage policy.")
            return redirect("arbiter:list-usage-policy")
    else:
        if can_change:
            form = UsagePolicyForm(instance=policy)
        else:
            form = UsagePolicyForm(instance=policy, disabled=True)

    context = {"form": form, "navbar": navbar(
        request), "can_change": can_change, "title": "Change Usage Policy"}
    return render(request, "arbiter/change_view.html", context)
