from django.core.management.base import BaseCommand, CommandError
from arbiter3.arbiter.models import Policy, Violation, Event
from django.utils import timezone


class Command(BaseCommand):
    help = "Cleans up violations in the database, and runs the service to reflect the changes."

    def add_arguments(self, parser):
        parser.add_argument("--before", type=str, required=True)
        parser.add_argument("--policies", nargs="+", type=str, required=False)

    def handle(self, before, *args, **options):
        before_time = timezone.datetime.fromisoformat(before)
        before_time = timezone.make_aware(before_time)
        policies = (
            Policy.objects.filter(name__in=options["policies"])
            if options["policies"]
            else Policy.objects.all()
        )

        selected_violations = Violation.objects.filter(
            policy__in=policies,
            timestamp__lte=before_time,
        )

        selected_violations.delete()

        selected_events = Event.objects.filter(
            timestamp__lte=before_time,
        )

        selected_events.delete()
