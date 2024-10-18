from django.shortcuts import render, redirect
from arbiter.models import UsagePolicy, BasePolicy, Policy, Limit
from .nav import navbar
from django import forms
from django.views.generic.list import ListView


USEC_PER_SEC = 1_000_000
BYTES_PER_GIB = 1024**3


def cores_to_usec(cores: float) -> int:
    usec = cores * USEC_PER_SEC
    if usec < 1:
        return 1
    return int(usec)


def usec_to_cores(usec: int) -> float:
    return usec / USEC_PER_SEC


def gib_to_bytes(gib: float) -> int:
    _bytes = gib * BYTES_PER_GIB
    if _bytes < 1:
        return 1
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
    cpu = forms.FloatField(label="CPU Cores", required=True)
    mem = forms.FloatField(label="Memory in GiB", required=True)
    class Meta:
        model = UsagePolicy
        fields = ["name", "domain", "description", "penalty_duration", "repeated_offense_scalar", "query", "grace_period", "repeated_offense_lookback"]
        widgets = {'grace_period': forms.TimeInput(), "repeated_offense_lookback": forms.TimeInput()}


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