from django.urls import reverse
from collections import defaultdict


class BarItem:
    def __init__(self, name, url, attributes = None):
        self.name = name
        self.url = url
        self.attr = attributes or {}

    def render(self):
        attributes = ' '.join([f'{k}={v}' for k, v in self.attr.items()])
        return f'<a {attributes} href="{self.url}">{self.name}</a>'

def navbar(request):
    routes = {
        "Base Policy": reverse("arbiter:list-base-policy"),
        "Usage Policy": reverse("arbiter:list-usage-policy"),
        "Status": "",
        "Constraint": "",
        "Dash": "",
    }

    items = []

    for name, url in routes.items():
        if request.path == url:
            items.append(BarItem(name, url, {"class": "active"}))
        else:
            items.append(BarItem(name, url))

    return items