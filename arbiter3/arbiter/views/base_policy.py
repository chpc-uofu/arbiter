from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django import forms
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from arbiter3.arbiter.models import BasePolicy, Limits, QueryData, QueryParameters, CPU_QUOTA, MEMORY_MAX
from arbiter3.arbiter.utils import usec_to_cores, bytes_to_gib, cores_to_usec, gib_to_bytes, regex_help_text
from arbiter3.arbiter.prop import CPU_QUOTA, MEMORY_MAX

from .nav import navbar


class BasePolicyListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = BasePolicy
    login_url = reverse_lazy("login")
    permission_required = "arbiter.arbiter_view"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        context["can_create"] = self.request.user.has_perm(
            "arbiter.arbiter_administrator")
        context["title"] = "Base Policies"
        return context


class BasePolicyForm(forms.ModelForm):
    cpu = forms.FloatField(label="CPU Limit in Cores", required=False, min_value=0,  help_text="CPU limit that will be applied to users in the domain as a base status")
    mem = forms.FloatField(label="Memory Limit in GiB", required=False, min_value=0, help_text="Memory limit that will be applied to users in the domain as a base status")

    user_whitelist = forms.CharField(
        label="Query User Whitelist",
        required=False,
        initial="arbiter|nobody", 
        help_text=regex_help_text("A regex for usernames which are whitelisted from recieving this base status"), 
        widget=forms.Textarea(attrs={'rows':3})
        )

    class Meta:
        model = BasePolicy
        fields = ["name", "domain", "description", "active"]

        help_texts = {
            'domain': regex_help_text("regex for the hostname/instance where this policy is in affect")
        }

    def __init__(self, *args, disabled=False, **kwargs):
        super().__init__(*args, **kwargs)

        if constraints := self.instance.penalty_constraints:
            for name, value in constraints['tiers'][0].items():
                if name == CPU_QUOTA:
                    self.fields['cpu'].initial = usec_to_cores(value)
                if name == MEMORY_MAX:
                    self.fields['mem'].initial = bytes_to_gib(value)

        if disabled:
            for field in self.fields.values():
                field.widget.attrs['disabled'] = True
        
        if query_data := self.instance.query_data:
            params = query_data.get("params")
            if params != None:
                self.fields['user_whitelist'].initial =  params.get("user_whitelist", "")

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
        policy.is_base_policy = True
        limits: Limits = {}
        if cpu_limit := self.cleaned_data['cpu']:
            limits[CPU_QUOTA] = cpu_limit
        if mem_limit := self.cleaned_data['mem']:
            limits[MEMORY_MAX] = mem_limit
        policy.penalty_constraints = {'tiers': [limits]}

        filters = f'instance=~"{self.cleaned_data["domain"]}"'
        params = None

        if whitelist := self.cleaned_data['user_whitelist']:
            filters += f', user!~"{whitelist}"'
            params = QueryParameters(0, 0, user_whitelist=self.cleaned_data["user_whitelist"])
        
        policy.query_data = QueryData.raw_query(f'cgroup_warden_cpu_usage_seconds{{{filters}}}', params).json()
        policy.save()


@login_required(login_url=reverse_lazy("login"))
def new_base_policy(request):
    can_change = request.user.has_perm("arbiter.arbiter_administrator")

    if not can_change:
        messages.error(
            request, "You do not have permissions to create a Base Policy")
        return redirect("arbiter:view-dashboard")

    if request.method == "POST":
        form = BasePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully created base policy.")
            return redirect("arbiter:list-base-policy")
    else:
        form = BasePolicyForm()

    context = {"form": form, "navbar": navbar(
        request), "can_change": can_change, "title": "New Base Policy"}
    return render(request, "arbiter/change_view.html", context)


@login_required(login_url=reverse_lazy("login"))
@permission_required('arbiter.arbiter_view')
def change_base_policy(request, policy_id):
    policy = BasePolicy.objects.filter(pk=policy_id).first()

    can_change = request.user.has_perm("arbiter.arbiter_administrator")

    if not policy:
        messages.error(request, "Base Policy not found.")
        return redirect("arbiter:list-base-policy")

    if request.method == "POST":
        if not can_change:
            messages.error(
                request, "You do not have permissions to change a Base Policy")
            return redirect(request.path_info)

        form = BasePolicyForm(request.POST, instance=policy)
        if "save" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Successfully changed base policy.")
            return redirect("arbiter:list-base-policy")
        if "delete" in request.POST:
            policy.delete()
            messages.success(request, "Successfully removed base policy.")
            return redirect("arbiter:list-base-policy")
    else:
        if can_change:
            form = BasePolicyForm(instance=policy)
        else:
            form = BasePolicyForm(instance=policy, disabled=True)

    context = {"form": form, "navbar": navbar(
        request), "can_change": can_change, "title": "Change Base Policy"}
    return render(request, "arbiter/change_view.html", context)
