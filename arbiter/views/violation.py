from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.contrib import messages
from django.utils import timezone

from arbiter.models import Violation

from .nav import navbar


class ViolationListView(ListView):
    model = Violation
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar"] = navbar(self.request)
        return context


def change_violation(request, violation_id):
    violation = Violation.objects.filter(pk=violation_id).first()

    if not violation:
        messages.error(request, "Violation not found.")
        return redirect("arbiter:list-violation")
    
    if request.method == "POST":
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
    
    context = {"violation": violation, "navbar": navbar(request)}
    return render(request, "arbiter/violation_detail.html", context)