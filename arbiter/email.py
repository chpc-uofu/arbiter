from arbiter.models import Violation
from arbiter import plots
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from django.conf import settings
import logging
from smtplib import SMTPException
from plotly.graph_objects import Figure

LOGGER = logging.getLogger(__name__)

def send_violation_email(violation: Violation | None):
    figures: dict[str, Figure] = dict(
        cpu_graph=plots.plot_violation_cpu_graph(violation),
        mem_graph=plots.plot_violation_memory_graph(violation),
        cpu_usage_pie=plots.plot_violation_proc_cpu_usage_pie(violation),
        mem_usage_pie=plots.plot_violation_proc_memory_usage_pie(violation),
    )
    user = settings.ARBITER_USER_LOOKUP(violation.target)
    LOGGER.info(f"Attempting to send violation mail to {user}")
    subject = f"Violation of usage policy {violation.policy} on {violation.target.host} by {user.username} ({user.realname})"
    text_content = f"Violation of usage policy {violation.policy} on {violation.target.host} by {user.username} ({user.realname})"
    message = EmailMultiAlternatives(subject, text_content, "arbiter", [user.email])

    for name, figure in figures.items():
        figure_bytes = figure.to_image(format="png", width=600, height=350, scale=2)
        image = MIMEImage(figure_bytes)
        image.add_header("Content-ID", f"<{name}>")
        message.attach(image)

    html_content = render_to_string("arbiter/email.html", {"figures": figures})
    message.attach_alternative(html_content, "text/html")
    message.mixed_subtype = "related"
    try:
        message.send(fail_silently=False)
    except SMTPException as e:
        LOGGER.error(f"Could not send email to {user.email} ({user.username} i.e. {user.realname}): {e}")

