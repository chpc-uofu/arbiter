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
    
    active_violations = Violation.objects.filter(target_id=target_id).exclude(expiration__lt = timezone.now())
    recent_violations = Violation.objects.filter(target_id=target_id, expiration__lt = timezone.now()).order_by("-timestamp")[:10]

    readable_limits = target.limits
    readable_limits = to_readable_limits(readable_limits)

    context = {"navbar": navbar(request),"title": "User Breakdown", "target": target, "limits":readable_limits, "active_violations": active_violations, "recent_violations": recent_violations}

    return render(request, "arbiter/user_breakdown.html", context)
