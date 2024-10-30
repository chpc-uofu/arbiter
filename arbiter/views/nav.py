from django.urls import reverse

class BarItem:
    def __init__(self, name, url, attributes=None):
        self.name = name
        self.url = url
        self.attr = attributes or {}

    def render(self):
        attributes = " ".join([f"{k}={v}" for k, v in self.attr.items()])
        return f'<a {attributes} href="{self.url}">{self.name}</a>'


def navbar(request):

    routes = {"Home": reverse("view-dashboard")}
    if request.user.is_authenticated:
        routes["Base Policy"] = reverse("list-base-policy")
    if request.user.is_authenticated:
        routes["Usage Policy"] = reverse("list-usage-policy")
    if request.user.is_authenticated:
        routes["Violations"] = reverse("list-violation")

    items = []

    for name, url in routes.items():
        if request.path == url:
            items.append(BarItem(name, url, {"class": "active"}))
        else:
            items.append(BarItem(name, url))

    return items
