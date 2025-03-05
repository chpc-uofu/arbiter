from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.utils import timezone

from arbiter3.arbiter.models import Target, Violation
from arbiter3.arbiter.utils import to_readable_limits
from .nav import navbar


@permission_required('arbiter.view_dashboard')
def get_user_lookup(request):
    if request.method == "POST":
        user = request.POST.get("user")

        targets = Target.objects.filter(username=user)

        if len(targets) == 0:
            messages.error(request, "Specified user is not in arbiter's records (this may be because the names are incorrect or the user has not gone into penalty/base status before)")
        else:
            return redirect("arbiter:user-breakdown", user)
    
    context = dict(
        title="User Lookup",
        navbar=navbar(request),
    )

    return render(request, "arbiter/user_lookup.html", context)


@permission_required('arbiter.view_dashboard')
def get_user_breakdown(request, username):
    targets = Target.objects.filter(username=username).values("host", "limits")

    for target in targets:
        target["limits"] = to_readable_limits(target["limits"])

    if len(targets) == 0:
        messages.error(request, "Usage Policy not found.")
        return redirect("arbiter:list-usage-policy")

    
    active_violations = Violation.objects.filter(target__username=username).exclude(expiration__lt = timezone.now())
    recent_violations = Violation.objects.filter(target__username=username, expiration__isnull=False).order_by("-timestamp")[:10]

    context = {"navbar": navbar(request),"title": "User Breakdown", "username":username, "targets": targets, "active_violations": active_violations, "recent_violations": recent_violations}

    return render(request, "arbiter/user_breakdown.html", context)
