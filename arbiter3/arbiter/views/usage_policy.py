from django.shortcuts import render, redirect
from django import forms
from django.views.generic.list import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy, reverse

import json
from dataclasses import dataclass

from arbiter3.arbiter.models import UsagePolicy, QueryData, QueryParameters, CPU_QUOTA, MEMORY_MAX
from arbiter3.arbiter.utils import usec_to_cores, bytes_to_gib, cores_to_usec, gib_to_bytes, regex_help_text

from .nav import navbar


@dataclass
class ConstraintTier:
    memory_gib: float = None
    cpu_cores: float = None


class TieredPenaltyWidget(forms.Widget):
    template_name = "arbiter/penalty_widget.html"

    def __init__(self, **kwargs):
        self.can_change = True
        super().__init__(**kwargs)

    class Media:
        css = {
            "all": []
        }
        js = ['js/tiers-widget.js',]

    def get_context(self, name: str, value, attrs=None):
        context = super().get_context(name, value, attrs)
        context['can_change'] = self.can_change
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
                tier.memory_gib = round(bytes_to_gib(mem_max), 2)

            if cpu_quota := tier_limits.get(CPU_QUOTA):
                tier.cpu_cores = round(usec_to_cores(cpu_quota), 2)

            view_constraints.append(tier)

        context['tiers'] = view_constraints
        return context


class UsagePolicyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = UsagePolicy
    login_url = reverse_lazy("login")
    permission_required = "arbiter.arbiter_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        context["can_create"] = self.request.user.has_perm(
            "arbiter.arbiter_administrator")
        context["title"] = "Usage Policies"
        return context


class UsagePolicyForm(forms.ModelForm):
    proc_whitelist = forms.CharField(
        label="Query Process Whitelist", 
        required=False, 
        help_text=regex_help_text("A regex for processes that will not be counted against user usage."), 
        widget=forms.Textarea(attrs={'rows':6, 'cols':100})
        )
    
    user_whitelist = forms.CharField(
        label="Query User Whitelist",
        required=False,
        initial="arbiter|nobody", 
        help_text=regex_help_text("A regex for usernames which are whitelisted from violating this policy"), 
        widget=forms.Textarea(attrs={'rows':3})
        )
    
    cpu_threshold = forms.FloatField(
        label="Query CPU Threshold", 
        required=False,
        help_text="Threshold in core seconds, that when above is considered bad usage"
        )
    
    mem_threshold = forms.FloatField(
        label="Query Memory Threshold",
        required=False,
        help_text="Threshold in GiB, that when above is considered bad usage"
        )
    #use_pss = forms.BooleanField(label="Use PSS memory", required=False, help_text="Use PSS (proprtional shared size) for memory usage evaluation. If disabled, uses RSS (default)")

    class Meta:
        model = UsagePolicy
        fields = ["name", "domain", "description", "penalty_duration", "repeated_offense_scalar",
                  "repeated_offense_lookback", "grace_period", "lookback", "active", "watcher_mode", "penalty_constraints"]
        widgets = {'grace_period': forms.TimeInput(), "repeated_offense_lookback": forms.TimeInput(
        ), "penalty_constraints": TieredPenaltyWidget}

        labels = {
            'active': 'Enabled'
        }

        help_texts = {
            'domain': regex_help_text("regex for the hostname/instance where this policy is in affect"),
            'lookback': "<span>How far back arbiter evaluates user's usage (e.g. if a user's average usage is above the threshold(s) for this amount of time, they will be in violation). <b>Should be at least twice as long as the configured scrape interval for the wardens on your TSDB.</b></span>",
        }

    def __init__(self, *args, disabled=False, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['use_pss'].initial = False
        self.fields['penalty_constraints'].widget.can_change = not disabled

        if query_data := self.instance.query_data:
            if cpu_threshold := query_data["params"]["cpu_threshold"]:
                self.fields['cpu_threshold'].initial = cpu_threshold
            if mem_threshold := query_data["params"]["mem_threshold"]:
                self.fields['mem_threshold'].initial = round(bytes_to_gib(mem_threshold), 3)
            # if use_pss := query_data["params"].get("use_pss_metric"):
            #     self.fields['use_pss'].initial = use_pss
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
        if not (cleaned_data["cpu_threshold"] or cleaned_data["mem_threshold"]):
            raise forms.ValidationError("At least one threshold (CPU or memory) is required.")

    def save(self, commit=True):
        policy = super().save(commit=False)
        policy.is_base_policy = True

        params = QueryParameters(
            cpu_threshold=self.cleaned_data["cpu_threshold"],
            mem_threshold=self.cleaned_data["mem_threshold"],
            user_whitelist=self.cleaned_data["user_whitelist"],
            proc_whitelist=self.cleaned_data["proc_whitelist"],
            use_pss_metric=True,
        )

        policy.query_data = QueryData.build_query(
            lookback=policy.lookback,
            domain=policy.domain,
            params=params
        ).json()

        policy.save()


@login_required(login_url=reverse_lazy("login"))
@permission_required('arbiter.arbiter_view')
def new_usage_policy(request):
    can_change = request.user.has_perm("arbiter.arbiter_administrator")

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
        if request.GET:
            form = UsagePolicyForm(request.GET)
        else:
            form = UsagePolicyForm()


    context = {"form": form, "navbar": navbar(
        request), "can_change": can_change, "title": "Create Usage Policy"}
    return render(request, "arbiter/usagepolicy_change.html", context)


@login_required(login_url=reverse_lazy("login"))
@permission_required('arbiter.arbiter_view')
def change_usage_policy(request, policy_id):
    policy = UsagePolicy.objects.filter(pk=policy_id).first()

    can_change = request.user.has_perm("arbiter.arbiter_administrator")

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
        if "copy" in request.POST:
            try:
                policy.pk = None
                policy.name += "(copy)"
                policy.active = False
                policy.save()

                messages.success(request, "Successfully copied usage policy.")
                url = reverse("arbiter:change-usage-policy", kwargs = {'policy_id' : policy.id})
                return redirect(url)
            except:
                messages.error(request, f"Unable to copy policy. Check that the name {policy.name} isn't taken.")
                return redirect("arbiter:list-usage-policy")

    else:
        if can_change:
            form = UsagePolicyForm(instance=policy)
        else:
            form = UsagePolicyForm(instance=policy, disabled=True)

    context = {"form": form, "navbar": navbar(
        request), "can_change": can_change, "title": "Change Usage Policy"}
    return render(request, "arbiter/usagepolicy_change.html", context)
