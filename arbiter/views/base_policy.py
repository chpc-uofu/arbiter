from django.shortcuts import render, redirect
from django import forms
from django.views.generic.list import ListView
from django.contrib import messages

from arbiter.models import BasePolicy, Limit, Query
from arbiter.utils import usec_to_cores, bytes_to_gib, cores_to_usec, gib_to_bytes

from .nav import navbar


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
            messages.success(request, "Successfully created base policy.")
            return redirect(f"arbiter:list-base-policy")
    else:
        form = BasePolicyForm()
    return render(request, "arbiter/change_view.html", {"form": form, "navbar": navbar(request)})


def change_base_policy(request, policy_id):
    policy = BasePolicy.objects.filter(pk=policy_id).first()

    if not policy:
        messages.error("Base Policy not found.")

    if request.method == "POST":
        form = BasePolicyForm(request.POST, instance=policy)
        if "save" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Successfully changed base policy.")
            return redirect(f"arbiter:list-base-policy")
        if "delete" in request.POST:
            policy.delete()
            messages.success(request, "Successfully removed base policy.")
            return redirect(f"arbiter:list-base-policy")
    else:
        form = BasePolicyForm(instance=policy)

    context = {"form": form, "navbar": navbar(request)}
    return render(request, "arbiter/change_view.html", context)