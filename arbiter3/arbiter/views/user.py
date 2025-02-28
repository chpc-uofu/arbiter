from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required
from django.contrib import messages

from arbiter3.arbiter.models import Target, Violation
from .nav import navbar


@permission_required('arbiter.view_dashboard')
def get_user_lookup(request):
    if request.method == "POST":
        host = request.POST.get("host")
        user = request.POST.get("user")

        if not (host and user):
            messages.error(request, "Both host and user required")
        else:
            target = Target.objects.filter(username=user, host=host).first()

            if not target:
                messages.error(request, "Specified host+user is not in arbiter's records (this may be because the names are incorrect or the user has not gone into penalty/base status before)")
            else:
                return redirect("arbiter:user-breakdown", target.id)
    
    context = dict(
        title="User Lookup",
        hosts=set(Target.objects.values_list("host", flat=True)),
        navbar=navbar(request),
    )

    return render(request, "arbiter/user_lookup.html", context)


@permission_required('arbiter.view_dashboard')
def get_user_breakdown(request, target_id):
    target = Target.objects.filter(pk=target_id).first()

    if not target:
        messages.error(request, "Usage Policy not found.")
        return redirect("arbiter:list-usage-policy")

    context = {"navbar": navbar(request), "target": target, "title": "User Breakdown"}

    return render(request, "arbiter/user_breakdown.html", context)
