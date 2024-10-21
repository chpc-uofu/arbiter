from django.shortcuts import render, redirect
from arbiter.models import UsagePolicy, BasePolicy, Policy, Limit, Query, QueryParameters
from .nav import navbar
from django import forms
from django.views.generic.list import ListView
import re


USEC_PER_SEC = 1_000_000
BYTES_PER_GIB = 1024**3
NSEC_PER_SEC = 1000**3

SEC_PER_MIN = 60
SEC_PER_HOUR = 60**2
SEC_PER_DAY = 60**2 * 24
SEC_PER_WEEK = 60**2 * 24 * 7

def sec_to_promtime(seconds: str):
    time_units = [
        (7 * 24 * 3600, 'w'), 
        (24 * 3600, 'd'),
        (3600, 'h'),
        (60, 'm'),
        (1, 's')
    ]
    components = []
    for unit_seconds, label in time_units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            components.append(f"{count}{label}")
            seconds %= unit_seconds
    return ''.join(components) if components else '0s'

def promtime_to_sec(time_str: str) -> int | None:
    total_seconds = 0
    pattern = r'(\d+)([wdhms])'
    matches = re.findall(pattern, time_str)
    if ''.join(f"{amount}{unit}" for amount, unit in matches) != time_str:
        return None
    unit_to_seconds = {
        'w': 7 * 24 * 3600,  # weeks
        'd': 24 * 3600,      # days
        'h': 3600,           # hours
        'm': 60,             # minutes
        's': 1               # seconds
    }
    for amount, unit in matches:
        total_seconds += int(amount) * unit_to_seconds[unit]
    return total_seconds

def cores_to_usec(cores: float) -> int:
    usec = cores * USEC_PER_SEC
    if usec < 1:
        return 1
    return int(usec)

def cores_to_nsec(cores: float) -> int:
    nsec = cores * NSEC_PER_SEC
    if nsec < 1:
        return 1
    return int(nsec)

def usec_to_cores(usec: int) -> float:
    return usec / USEC_PER_SEC

def nsec_to_cores(nsec: int) -> float:
    return nsec / NSEC_PER_SEC

def gib_to_bytes(gib: float) -> int:
    _bytes = gib * BYTES_PER_GIB
    return int(_bytes)

def bytes_to_gib(byts: int) -> float:
    return byts / BYTES_PER_GIB


class UsagePolicyListView(ListView):
    model = UsagePolicy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
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

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if constraints := self.instance.penalty_constraints:
            for c in constraints:
                if c["name"] == "CPUQuotaPerSecUSec" and c["value"]:
                    self.fields['cpu_limit'].initial = usec_to_cores(c["value"])
                if c["name"] == "MemoryMax" and c["value"]:
                    self.fields['mem_limit'].initial = bytes_to_gib(c["value"])

        if query := self.instance.query:
            if cpu_threshold := query["params"]["cpu_threshold"]:
                self.fields['cpu_threshold'].initial = nsec_to_cores(cpu_threshold)
            if mem_threshold := query["params"]["mem_threshold"]:
                self.fields['mem_threshold'].initial = bytes_to_gib(mem_threshold)
            self.fields['proc_whitelist'].initial = query["params"]["proc_whitelist"]
            self.fields['user_whitelist'].initial = query["params"]["user_whitelist"]

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
        policy.query = Query.build_query(
            lookback=policy.lookback,
            domain=policy.domain, 
            params=params
        ).json()
        
        policy.save()


def new_usage_policy(request):
    if request.method == "POST":
        form = UsagePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"arbiter:list-usage-policy")
    else:
        form = UsagePolicyForm()
    return render(request, "arbiter/change_view.html", {"form": form, "navbar": navbar(request)})


def change_usage_policy(request, id):
    policy = UsagePolicy.objects.get(pk=id)

    if policy.is_base_policy:
        return redirect("arbiter:change-base-policy", id)

    if request.method == "POST":
        form = UsagePolicyForm(request.POST, instance=policy)
        if "save" in request.POST and form.is_valid():
            form.save()
            return redirect(f"arbiter:list-base-policy")
        if "delete" in request.POST:
            policy.delete()
            return redirect(f"arbiter:list-base-policy")
    else:
        form = UsagePolicyForm(instance=policy)

    return render(request, "arbiter/change_view.html", {"form": form, "navbar": navbar(request)})


class BasePolicyListView(ListView):
    model = BasePolicy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        return context
    

class BasePolicyForm(forms.ModelForm):
    cpu = forms.FloatField(label="CPU Cores", required=False)
    mem = forms.FloatField(label="Memory in GiB", required=False)

    class Meta:
        model = BasePolicy
        fields = ["name", "domain", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if constraints := self.instance.penalty_constraints:
            for c in constraints:
                if c["name"] == "CPUQuotaPerSecUSec" and c["value"]:
                    self.fields['cpu'].initial = usec_to_cores(c["value"])
                if c["name"] == "MemoryMax" and c["value"]:
                    self.fields['mem'].initial = bytes_to_gib(c["value"])

    def clean_cpu(self):
        if cpu := self.cleaned_data["cpu"]:
            return cores_to_usec(cpu)
        return None
    
    def clean_mem(self):
        if mem := self.cleaned_data["mem"]:
            return gib_to_bytes(mem)
        return None
    
    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data["cpu"] or cleaned_data["mem"]):
            raise forms.ValidationError("Either CPU or Memory must be set")
        
    def save(self, commit=True):
        policy = super().save(commit=False)
        policy.is_base_policy=True
        limits = []
        if cpu_limit := self.cleaned_data['cpu']:
            limits.append(Limit.cpu_quota(cpu_limit).json())
        if mem_limit := self.cleaned_data['mem']:
            limits.append(Limit.memory_max(mem_limit).json())
        policy.penalty_constraints = limits
        policy.query = Query.raw_query(f'systemd_unit_cpu_usage_ns{{instance=~"{policy.domain}"}}').json()
        policy.save()


def new_base_policy(request):
    if request.method == "POST":
        form = BasePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"arbiter:list-base-policy")
    else:
        form = BasePolicyForm()
    return render(request, "arbiter/change_view.html", {"form": form, "navbar": navbar(request)})


def change_base_policy(request, id):
    policy = BasePolicy.objects.get(pk=id)

    if not policy.is_base_policy:
        return redirect("arbiter:change-usage-policy", id)
    
    if request.method == "POST":
        form = BasePolicyForm(request.POST, instance=policy)
        if "save" in request.POST and form.is_valid():
            form.save()
            return redirect(f"arbiter:list-base-policy")
        if "delete" in request.POST:
            policy.delete()
            return redirect(f"arbiter:list-base-policy")
    else:
        form = BasePolicyForm(instance=policy)

    return render(request, "arbiter/change_view.html", {"form": form, "navbar": navbar(request)})