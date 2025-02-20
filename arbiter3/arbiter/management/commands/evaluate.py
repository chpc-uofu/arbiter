from django.core.management.base import BaseCommand
from arbiter3.arbiter.eval import evaluate
from django.utils import timezone
from arbiter3.arbiter.models import Policy
from time import sleep


class Command(BaseCommand):
    help = "Runs the entire arbiter service (Gets violations and applies penalties)"

    def add_arguments(self, parser):
        parser.add_argument("--policies", nargs="+", type=str)
        parser.add_argument("-S", "--seconds", default=0, type=int)
        parser.add_argument("-M", "--minutes", default=0, type=int)
        parser.add_argument("-H", "--hours", default=0, type=int)

    def handle(self, *args, **options):
        seconds = options["seconds"]
        minutes = options["minutes"]
        hours = options["hours"]

        cycle_time = timezone.timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        ).total_seconds()

        while True:
            if options["policies"]:
                policies = Policy.objects.filter(name__in=options["policies"])
            else:
                policies = Policy.objects.all()

            evaluate(policies)
            sleep(cycle_time)
            if cycle_time == 0:
                break
