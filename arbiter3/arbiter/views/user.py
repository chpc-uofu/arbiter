from django.forms.renderers import BaseRenderer
from django.shortcuts import render, redirect
from django import forms
from django.utils.safestring import mark_safe
from django.views.generic.list import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.decorators import permission_required

from arbiter3.arbiter.models import Target, Violation
from .nav import navbar

@permission_required('arbiter.view_dashboard')
def get_user_lookup(request):

    context = dict(
        title="User Lookup",
        navbar=navbar(request)
    )

    return render(request, "arbiter/user_lookup.html", context)

@permission_required('arbiter.view_dashboard')
def get_user_breakdown(request, target_id):
    target = Target.objects.filter(pk=target_id).first()

    if not target:
        messages.error(request, "Usage Policy not found.")
        return redirect("arbiter:list-usage-policy")

    context = {"navbar": navbar(
        request), "title": "Change Usage Policy"}

    return render(request, "arbiter/change_view.html", context)
