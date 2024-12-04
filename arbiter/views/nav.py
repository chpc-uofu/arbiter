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

    routes = {}

    if request.user.is_authenticated:
        routes["Dashboard"] = reverse("arbiter:view-dashboard")
        routes["Base Policy"] = reverse("arbiter:list-base-policy")
        routes["Usage Policy"] = reverse("arbiter:list-usage-policy")
        routes["Violations"] = reverse("arbiter:list-violation")

    items = []

    for name, url in routes.items():
        if request.path == url:
            items.append(BarItem(name, url, {"class": "active"}))
        else:
            items.append(BarItem(name, url))

    return items
