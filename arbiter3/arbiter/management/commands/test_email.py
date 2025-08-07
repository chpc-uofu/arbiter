import logging

from django.core import mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from jinja2 import Environment, FileSystemLoader

from arbiter3.arbiter.conf import ARBITER_ADMIN_EMAILS, ARBITER_FROM_EMAIL, ARBITER_USER_LOOKUP
from arbiter3.arbiter.models import Violation
from arbiter3.arbiter.email import send_email, format_limits
from arbiter3.arbiter.plots import QueryError, violation_cpu_usage_figure, violation_mem_usage_figure 


class Command(BaseCommand):
    help = "Sends a test email to the given recipients"

    def add_arguments(self, parser):
        parser.add_argument("--recipients", nargs="+", type=str)
        parser.add_argument('--violation', action='store_true')

    def handle(self, *args, **options):
        if test_violation := options['violation']:
            result = send_test_violation_mail(options['recipients'])
        else:
            result = send_test_email(options['recipients'])
        
        print(result)


def convert_to_local_timezone(utctime):
    return utctime.astimezone(timezone.get_current_timezone())


def send_test_email(recipients: list[str]) -> str:
    if not recipients:
        return f'No recipients specified'

    subject = f"Arbiter3 test email"
    body = f"This is a test email from the Arbiter3 service."

    try:
        mail.send_mail(subject, body, ARBITER_FROM_EMAIL, recipients, fail_silently=False)
    except Exception as e:
        return f"Could not send email to {recipients}: {e}"
    return f"Sent mail to recipients {recipients} successfully"


def send_test_violation_mail(recipients: list[str]) -> str:
    violation = Violation.objects.filter(expiration__isnull=False).last()
    if not violation:
        return "No violatons found"

    username, realname, email = ARBITER_USER_LOOKUP(violation.target.username)

    try:
        cpu = violation_cpu_usage_figure(violation)
        mem = violation_mem_usage_figure(violation)
    except QueryError as e:
        return f'Could not send email to {recipients}: error generating figures: {e}'

    figures = dict(cpu_chart=cpu, mem_chart=mem)
    if not figures:
        return f'Could not send email to {recipients}: no figures generated'

    context = dict(
        username=username,
        realname=email,
        limits=format_limits(violation.limits),
        violation=violation,
        timestamp=convert_to_local_timezone(violation.timestamp),
        expiration=convert_to_local_timezone(violation.expiration),
    )

    try:
        send_email(recipients, figures, context)
    except Exception as e:
        return f'Could not send email to {recipients}: {e}'
    
    return f"Sent mail to {recipients} successfully"