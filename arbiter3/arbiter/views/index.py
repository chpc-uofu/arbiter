
from django.shortcuts import render
from arbiter3.arbiter.views.nav import navbar


def view_index(request):
    context = dict(
        title="Home",
        navbar=navbar(request)
    )

    return render(request, "arbiter/base.html", context)
