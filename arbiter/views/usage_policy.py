from django.shortcuts import render, redirect
from django import forms
from django.views.generic.list import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

from arbiter.models import UsagePolicy, Limit, QueryData, QueryParameters
from arbiter.utils import usec_to_cores, bytes_to_gib, cores_to_usec, gib_to_bytes, cores_to_nsec, nsec_to_cores

from .nav import navbar

class UsagePolicyListView(LoginRequiredMixin, ListView):
    model = UsagePolicy
    login_url = reverse_lazy("arbiter:login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        context["can_create"] = self.request.user.has_perm("arbiter.add_usagepolicy")
        return context


class UsagePolicyForm(forms.ModelForm):
    cpu_limit = forms.FloatField(label="Penalty CPU Limit", required=False)
    mem_limit = forms.FloatField(label="Penalty Memory Limit", required=False)
    proc_whitelist = forms.CharField(label="Query Process Whitelist", required=False)
    user_whitelist = forms.CharField(label="Query User Whitelist", required=False)
    cpu_threshold = forms.FloatField(label="Query CPU Threshold", required=False)
    mem_threshold = forms.FloatField(label="Query Memory Threshold", required=False)

    class Meta:
        model = UsagePolicy
        fields = ["name", "domain", "description", "penalty_duration", "repeated_offense_scalar", 
                  "grace_period", "repeated_offense_lookback", "lookback"]
        widgets = {'grace_period': forms.TimeInput(), "repeated_offense_lookback": forms.TimeInput()}

    
    def __init__(self, *args, disabled=False, **kwargs):
        super().__init__(*args, **kwargs)
        if constraints := self.instance.penalty_constraints:
            for c in constraints:
                if c["name"] == "CPUQuotaPerSecUSec" and c["value"]:
                    self.fields['cpu_limit'].initial = usec_to_cores(c["value"])
                if c["name"] == "MemoryMax" and c["value"]:
                    self.fields['mem_limit'].initial = bytes_to_gib(c["value"])

        if query_data := self.instance.query_data:
            if cpu_threshold := query_data["params"]["cpu_threshold"]:
                self.fields['cpu_threshold'].initial = nsec_to_cores(cpu_threshold)
            if mem_threshold := query_data["params"]["mem_threshold"]:
                self.fields['mem_threshold'].initial = bytes_to_gib(mem_threshold)
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
    
    def clean_cpu_threshold(self):
        if cpu := self.cleaned_data["cpu_threshold"]:
            return cores_to_nsec(cpu)
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
        if not (cleaned_data["cpu_limit"] or cleaned_data["mem_limit"]):
            raise forms.ValidationError("At least one limit (CPU or memory) is required.")
    
    def save(self, commit=True):
        policy = super().save(commit=False)
        policy.is_base_policy=True
        limits = []
        if mem_limit := self.cleaned_data["mem_limit"]:
            limits.append(Limit.memory_max(mem_limit).json())

        if cpu_limit := self.cleaned_data["cpu_limit"]:
            limits.append(Limit.cpu_quota(cpu_limit).json())

        policy.penalty_constraints = limits
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


@login_required(login_url=reverse_lazy("arbiter:login"))
def new_usage_policy(request):
    can_change = request.user.has_perm("arbiter.add_usagepolicy")

    if not can_change:
        messages.error(request, "You do not have permissions to create a Usage Policy")
        return redirect("arbiter:view-dashboard")

    if request.method == "POST":
        form = UsagePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully created usage policy.")
            return redirect(f"arbiter:list-usage-policy")
    else:
        form = UsagePolicyForm()

    context = {"form": form, "navbar": navbar(request), "can_change": can_change}
    return render(request, "arbiter/change_view.html", context)


@login_required(login_url=reverse_lazy("arbiter:login"))
def change_usage_policy(request, policy_id):
    policy = UsagePolicy.objects.filter(pk=policy_id).first()
    
    can_change = request.user.has_perm("arbiter.change_usagepolicy")

    if not policy:
        messages.error(request, "Usage Policy not found.")
        return redirect("arbiter:list-usage-policy")

    if request.method == "POST":
        if not can_change:
            messages.error(request, "You do not have permissions to change a Usage Policy")
            return redirect(request.path_info)

        form = UsagePolicyForm(request.POST, instance=policy)
        if "save" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Successfully changed usage policy.")
            return redirect(f"arbiter:list-usage-policy")
        if "delete" in request.POST:
            policy.delete()
            messages.success(request, "Successfully removed usage policy.")
            return redirect(f"arbiter:list-usage-policy")
    else:
        if can_change:
            form = UsagePolicyForm(instance=policy)
        else:
            form = UsagePolicyForm(instance=policy, disabled=True)

    context = {"form": form, "navbar": navbar(request), "can_change": can_change}
    return render(request, "arbiter/change_view.html", context)