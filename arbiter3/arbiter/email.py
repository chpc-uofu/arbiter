import logging
from email.mime.image import MIMEImage

from arbiter3.arbiter.models import Violation
from arbiter3.arbiter import plots
from arbiter3.arbiter.conf import ARBITER_USER_LOOKUP, ARBITER_ADMIN_EMAILS, ARBITER_NOTIFY_USERS, ARBITER_FROM_EMAIL

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


user_lookup = ARBITER_USER_LOOKUP


def send_violation_email(violation: Violation | None) -> str:

    username, realname, email = user_lookup(violation.target.username)

    recipients = ARBITER_ADMIN_EMAILS
    if ARBITER_NOTIFY_USERS and email:
        recipients.append(email)

    if not recipients:
        return f'No recipients specified, skipping email delivery.'

    try:
        cpu = plots.violation_cpu_usage_figure(violation)
        mem = plots.violation_mem_usage_figure(violation)
    except plots.QueryError as e:
        return f'Unable to create violation plots: {e}'

    figures = dict(cpu_chart=cpu, mem_chart=mem)

    subject = f"Violation of usage policy {violation.policy} on {violation.target.host} by {username} ({realname})"
    text_content = f"Violation of usage policy {violation.policy} on {violation.target.host} by {username} ({realname})"
    message = EmailMultiAlternatives(
        subject, text_content, ARBITER_FROM_EMAIL, recipients)

    if not figures:
        return f'Could not send email to {username} at {email} ({realname}): no figures generated'

    for name, figure in figures.items():
        fig_bytes = figure.to_image(
            format="png", width=600, height=350, scale=2)
        image = MIMEImage(fig_bytes)
        image.add_header("Content-ID", f"<{name}>")
        message.attach(image)

    html_content = render_to_string("arbiter/email.html", {"figures": figures})
    message.attach_alternative(html_content, "text/html")
    message.mixed_subtype = "related"
    try:
        message.send(fail_silently=False)
    except Exception as e:
        return f"Could not send email to {username} at {email} ({realname}): {e}"
    return f"Sent mail to {username} at {email} ({realname}) successfully."
