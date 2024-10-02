from arbiter.models import Violation
from arbiter import plots
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
import logging
from smtplib import SMTPException
from plotly.graph_objects import Figure
from arbiter.integrations import arbiter_user_lookup

LOGGER = logging.getLogger(__name__)

def send_violation_email(violation: Violation | None):
    cpu_chart, cpu_pie = plots.violation_cpu_usage_figures(violation)
    mem_chart, mem_pie = plots.violation_mem_usage_figures(violation)

    figures: dict[str, Figure] = dict(
        cpu_chart=cpu_chart,
        cpu_pie=cpu_pie,
        mem_chart=mem_chart,
        mem_pie=mem_pie
    )
    user = arbiter_user_lookup(violation.target)
    LOGGER.info(f"Attempting to send violation mail to {user}")
    subject = f"Violation of usage policy {violation.policy} on {violation.target.host} by {user.username} ({user.realname})"
    text_content = f"Violation of usage policy {violation.policy} on {violation.target.host} by {user.username} ({user.realname})"
    message = EmailMultiAlternatives(subject, text_content, "arbiter", [user.email])

    for name, figure in figures.items():
        fig_bytes = figure.to_image(format="png", width=600, height=350, scale=2)
        image = MIMEImage(fig_bytes)
        image.add_header("Content-ID", f"<{name}>")
        message.attach(image)

    html_content = render_to_string("arbiter/email.html", {"figures": figures})
    message.attach_alternative(html_content, "text/html")
    message.mixed_subtype = "related"
    try:
        message.send(fail_silently=False)
    except SMTPException as e:
        LOGGER.error(f"Could not send email to {user.email} ({user.username} i.e. {user.realname}): {e}")
