from django.core.management.base import BaseCommand
from arbiter3.arbiter.eval import evaluate, refresh_limits, logger
from django.utils import timezone
from django.db.utils import OperationalError
from arbiter3.arbiter.models import Policy
from arbiter3.arbiter.utils import promtime_to_sec
from time import sleep

class Command(BaseCommand):
    help = "Runs the entire arbiter service (Gets violations and applies penalties)"

    def add_arguments(self, parser):
        parser.add_argument("--policies", nargs="+", type=str)
        parser.add_argument("-S", "--seconds", default=0, type=int)
        parser.add_argument("-M", "--minutes", default=0, type=int)
        parser.add_argument("-H", "--hours", default=0, type=int)
        parser.add_argument("--refresh-interval", default="10m", type=str)

    def handle(self, *args, **options):
        seconds = options["seconds"]
        minutes = options["minutes"]
        hours = options["hours"]

        cycle_time = timezone.timedelta(seconds=seconds, minutes=minutes, hours=hours).total_seconds()
        refresh_time = promtime_to_sec(options["refresh_interval"])

        seconds_since_last_refresh = refresh_time

        while True:
            try:
                if options["policies"]:
                    policies = Policy.objects.filter(name__in=options["policies"])
                else:
                    policies = Policy.objects.all()
                
                seconds_since_last_refresh += cycle_time
                if seconds_since_last_refresh >= refresh_time:
                    seconds_since_last_refresh = 0
                    for policy in policies:
                        refresh_limits(policy)
                
                evaluate(policies)
                sleep(cycle_time)
                if cycle_time == 0:
                    break
                    
            except OperationalError:
                logger.warning('evaluate loop failed to complete on operation error, likely an issue with concurency with sqlite locking the database')