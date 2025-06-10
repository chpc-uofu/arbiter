from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone

from arbiter3.arbiter.models import Violation


#Export metrics of the format: "arbiter_violation{host=..., user=..., policy=...} = offense tier"
def violation_metrics_scrape(request):
    unexpired_violations_metrics = (
        Violation.objects.filter(expiration__gte=timezone.now(), is_base_status=False, policy__active=True)
    ).prefetch_related("policy")

    metric_name = "arbiter_violation"

    exported_str = f"""# HELP {metric_name} The offense count (penalty tier) of a currntly active violation\n# TYPE {metric_name} gauge\n"""

    for violation in unexpired_violations_metrics:
        labels = f'policy="{violation.policy.name}", host="{violation.target.host}", user="{violation.target.username}"'
        exported_str += f'{metric_name}{{{labels}}} {violation.penalty_tier + 1}'

    return HttpResponse(exported_str, content_type="text")