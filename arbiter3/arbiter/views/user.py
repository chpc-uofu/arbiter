from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.utils import timezone

from arbiter3.arbiter.models import Target, Violation
from arbiter3.arbiter.utils import to_readable_limits
from .nav import navbar
from arbiter3.arbiter.conf import ARBITER_USER_LOOKUP

try:
    user_lookup = ARBITER_USER_LOOKUP
except ImportError:
    def no_lookup(username: str):
        return "unknown", "unknown", "unknown"
    user_lookup = no_lookup


@permission_required('arbiter.arbiter_view')
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


@permission_required('arbiter.arbiter_view')
def get_user_breakdown(request, username):
    targets = Target.objects.filter(username=username).values("host", "limits")

    for target in targets:
        target["limits"] = to_readable_limits(target["limits"])

    if len(targets) == 0:
        messages.error(request, "Specified user is not in arbiter's records (this may be because the names are incorrect or the user has not gone into penalty/base status before)")
        return redirect("arbiter:user-lookup")
    
    active_violations = Violation.objects.filter(target__username=username, policy__active=True).exclude(expiration__lt = timezone.now())
    recent_violations = Violation.objects.filter(target__username=username, is_base_status=False, policy__active=True).order_by("-timestamp")[:10]

    username, realname, email = user_lookup(username)

    context = {
        "navbar": navbar(request),
        "title": "User Breakdown", 
        "username": username,
        "realname": realname,
        "email": email if not email.endswith("@localhost") else "unknown",
        "targets": targets, 
        "active_violations": active_violations, 
        "recent_violations": recent_violations
        }

    return render(request, "arbiter/user_breakdown.html", context)
