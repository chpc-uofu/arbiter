import logging
from email.mime.image import MIMEImage


from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from plotly.graph_objects import Figure

from arbiter3.arbiter.models import Violation
from arbiter3.arbiter import plots
from arbiter3.arbiter.conf import ARBITER_USER_LOOKUP, ARBITER_ADMIN_EMAILS, ARBITER_NOTIFY_USERS, ARBITER_FROM_EMAIL, ARBITER_EMAIL_TEMPLATE_DIR
from arbiter3.arbiter.utils import bytes_to_gib, usec_to_cores 

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from arbiter3.arbiter.prop import CPU_QUOTA, MEMORY_MAX

logger = logging.getLogger(__name__)
user_lookup = ARBITER_USER_LOOKUP
jinja_env = Environment(loader=FileSystemLoader(ARBITER_EMAIL_TEMPLATE_DIR))
body_template = jinja_env.get_template('email_body.html')
subject_template = jinja_env.get_template('email_subject.html')


def format_limits(limits: dict[str, int]) -> dict[str, str]:
    results = {}
    for limit, value in limits.items():
        if limit == CPU_QUOTA:
            results['CPU'] = round(usec_to_cores(value), 2)
        if limit == MEMORY_MAX:
            results['Memory'] = round(bytes_to_gib(value), 2)
    
    return results


def convert_to_local_timezone(utctime):
    return utctime.astimezone(timezone.get_current_timezone())


def send_email(recipients: list[str], figures: dict[str, Figure], context: dict[str,str]) -> str:
    subject = subject_template.render(**context)
    body = body_template.render(figures=figures, **context)
    message = EmailMultiAlternatives(subject, body, ARBITER_FROM_EMAIL, recipients, bcc=ARBITER_ADMIN_EMAILS)

    for name, figure in figures.items():
        fig_bytes = figure.to_image(format="png", width=600, height=350, scale=2)
        image = MIMEImage(fig_bytes)
        image.add_header("Content-ID", f"<{name}>")
        message.attach(image)

    message.attach_alternative(body, "text/html")
    message.mixed_subtype = "related"
    message.send(fail_silently=False)


def send_violation_email(violation: Violation | None) -> str:
    username, realname, email = user_lookup(violation.target.username)

    recipients = []
    if ARBITER_NOTIFY_USERS and email:
        recipients.append(email)

    if not recipients and ARBITER_NOTIFY_USERS:
        logger.warning(f"Could not find email for {violation.target.username}")

    try:
        cpu = plots.violation_cpu_usage_figure(violation)
        mem = plots.violation_mem_usage_figure(violation)
    except plots.QueryError as e:
        return f'Could not send email to {recipients}: error generating figures: {e}'

    figures = dict(cpu_chart=cpu, mem_chart=mem)
    if not figures:
        return f'Could not send email to {recipients}: no figures generated'

    context = dict(
        username=username,
        realname=realname,
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
