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
    cpu_limit = forms.FloatField(label="Penalty CPU Limit")
    mem_limit = forms.FloatField(label="Penalty Memory Limit")
    proc_whitelist = forms.CharField(label="Query Process Whitelist", required=False)
    user_whitelist = forms.CharField(label="Query User Whitelist", required=False)
    cpu_threshold = forms.FloatField(label="Query CPU Threshold")
    mem_threshold = forms.FloatField(label="Query Memory Threshold")

    class Meta:
        model = UsagePolicy
        fields = ["name", "domain", "description", "penalty_duration", "repeated_offense_scalar", "grace_period", "repeated_offense_lookback", "lookback"]
        widgets = {'grace_period': forms.TimeInput(), "repeated_offense_lookback": forms.TimeInput()}

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if constraints := self.instance.penalty_constraints:
            for c in constraints:
                if c["name"] == "CPUQuotaPerSecUSec":
                    self.fields['cpu_limit'].initial = usec_to_cores(c["value"])
                if c["name"] == "MemoryMax":
                    self.fields['mem_limit'].initial = bytes_to_gib(c["value"])

        if query := self.instance.query:
            self.fields['cpu_threshold'].initial = nsec_to_cores(query["params"]["cpu_threshold"])
            self.fields['mem_threshold'].initial = bytes_to_gib(query["params"]["mem_threshold"])
            self.fields['proc_whitelist'].initial = query["params"]["proc_whitelist"]
            self.fields['user_whitelist'].initial = query["params"]["user_whitelist"]

    def clean_cpu_limit(self):
        cpu = self.cleaned_data["cpu_limit"]
        return cores_to_usec(cpu)
    
    def clean_mem_limit(self):
        mem = self.cleaned_data["mem_limit"]
        return gib_to_bytes(mem)
    
    def clean_cpu_threshold(self):
        cpu = self.cleaned_data["cpu_threshold"]
        return cores_to_nsec(cpu)
    
    def clean_mem_threshold(self):
        mem = self.cleaned_data["mem_threshold"]
        b = gib_to_bytes(mem)
            #self.add_error('mem_threshold', "Please specify time at address if less than 3 years.")
        return b
    
    def clean_user_whitelist(self):
        whitelist = self.cleaned_data["user_whitelist"] or None
        return whitelist
    
    def clean_proc_whitelist(self):
        whitelist = self.cleaned_data["proc_whitelist"] or None
        return whitelist
    
    def save(self, commit=True):
        policy = super().save(commit=False)
        policy.is_base_policy=True

        policy.penalty_constraints = Limit.to_json(
            Limit.cpu_quota(self.cleaned_data["cpu_limit"]),
            Limit.memory_max(self.cleaned_data['mem_limit']),
        )
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
        if "save" in request.POST:
            form = UsagePolicyForm(request.POST, instance=policy)
            if form.is_valid():
                form.save()
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
    cpu = forms.FloatField(label="CPU Cores", required=True)
    mem = forms.FloatField(label="Memory in GiB", required=True)

    class Meta:
        model = BasePolicy
        fields = ["name", "domain", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if constraints := self.instance.penalty_constraints:
            for c in constraints:
                if c["name"] == "CPUQuotaPerSecUSec":
                    self.fields['cpu'].initial = usec_to_cores(c["value"])
                if c["name"] == "MemoryMax":
                    self.fields['mem'].initial = bytes_to_gib(c["value"])

    def clean_cpu(self):
        cpu = self.cleaned_data["cpu"]
        return cores_to_usec(cpu)
    
    def clean_mem(self):
        mem = self.cleaned_data["mem"]
        return gib_to_bytes(mem)

    def save(self, commit=True):
        policy = super().save(commit=False)
        policy.is_base_policy=True
        cpu_quota = Limit.cpu_quota(self.cleaned_data['cpu'])
        memory_max = Limit.memory_max(self.cleaned_data['mem'])
        constraints = Limit.to_json(cpu_quota, memory_max)
        policy.penalty_constraints = constraints
        policy.query = Query.raw_query(f'systemd_unit_cpu_usage_ns{{instance=~"{policy.domain}"}}').json()
        policy.save()


def new_base_policy(request):
    if request.method == "POST":
        form = BasePolicyForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            if Policy.objects.filter(name=name).exists():
                raise forms.ValidationError("Policy with that name already exists")
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
        if "save" in request.POST:
            form = BasePolicyForm(request.POST, instance=policy)
            if form.is_valid():
                form.save()
        if "delete" in request.POST:
            policy.delete()
        return redirect(f"arbiter:list-base-policy")
    else:
        form = BasePolicyForm(instance=policy)

    return render(request, "arbiter/change_view.html", {"form": form, "navbar": navbar(request)})