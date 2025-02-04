from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

from arbiter.conf import ARBITER_USER_LOOKUP
from arbiter.models import Violation
from django.utils.module_loading import import_string
from .nav import navbar

try:
    user_lookup = import_string(ARBITER_USER_LOOKUP)
except ImportError:
    def no_lookup(username:str):
        return "unknown","unknown","unknown"
    user_lookup = no_lookup


class ViolationListView(LoginRequiredMixin, ListView):
    model = Violation
    login_url = reverse_lazy("login")
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        context["title"] = "Violations"
        return context


@login_required(login_url=reverse_lazy("login"))
def change_violation(request, violation_id):
    violation = Violation.objects.filter(pk=violation_id).first()
    username, realname, email = user_lookup(violation.target.username)
    can_change = request.user.has_perm("arbiter.change_violation")

    if not violation:
        messages.error(request, "Violation not found.")
        return redirect("arbiter:list-violation")
    
    if request.method == "POST":
        if not can_change:
            messages.error(request, "You do not have permissions to change a Violation")
            return redirect(request.path_info)

        if "expire" in request.POST:
            if violation.expired:
                messages.warning(request, "Violation already expired.")
            else:
                violation.expiration = timezone.now()
                violation.save()
                messages.success(request, "Successfully expired violation.")
                return redirect("arbiter:list-violation")
        if "delete" in request.POST:
            violation.delete()
            messages.success(request, "Successfully removed violation.")
            return redirect("arbiter:list-violation")
    
    context = {"violation": violation, "realname":realname, "navbar": navbar(request), "can_change": can_change, "title": "Change Violation"}
    return render(request, "arbiter/violation_detail.html", context)