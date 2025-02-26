import logging

from django.core import mail
from django.core.management.base import BaseCommand

from arbiter3.arbiter.conf import ARBITER_ADMIN_EMAILS, ARBITER_FROM_EMAIL


class Command(BaseCommand):
    help = "Sends a test email to the given recipients"

    def add_arguments(self, parser):
        parser.add_argument("--recipients", nargs="+", type=str)

    def handle(self, *args, **options):
        result = send_test_email(options['recipients'])
        print(result)


def send_test_email(recipients: list[str]) -> str:

    recipients = recipients or ARBITER_ADMIN_EMAILS

    if not recipients:
        return f'No recipients specified'

    subject = f"Arbiter3 test email"
    body = f"This is a test email from the Arbiter3 service."

    try:
        mail.send_mail(subject, body, ARBITER_FROM_EMAIL, recipients, fail_silently=False)
    except Exception as e:
        return f"Could not send email to {recipients}: {e}"
    return f"Sent mail to recipients {recipients} successfully"