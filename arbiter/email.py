import logging
from email.mime.image import MIMEImage

from arbiter.models import Violation
from arbiter import plots
from arbiter.conf import ARBITER_USER_LOOKUP

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plotly.graph_objects import Figure


logger = logging.getLogger(__name__)

user_lookup = import_string(ARBITER_USER_LOOKUP)


def send_violation_email(violation: Violation | None) -> str:
    figures : dict[str: Figure] = dict()

    if cpu_figures := plots.violation_cpu_usage_figures(violation):
        figures['cpu_chart'] = cpu_figures.chart
        figures['cpu_pie'] = cpu_figures.pie

    if mem_figures := plots.violation_mem_usage_figures(violation):
        figures['mem_chart'] = mem_figures.chart
        figures['mem_pie'] = mem_figures.pie

    username, realname, email = user_lookup(violation.target.username)
    logger.info(
        f"Attempting to send violation mail to {username} at {email} ({realname})"
    )
    subject = f"Violation of usage policy {violation.policy} on {violation.target.host} by {username} ({realname})"
    text_content = f"Violation of usage policy {violation.policy} on {violation.target.host} by {username} ({realname})"
    message = EmailMultiAlternatives(subject, text_content, "arbiter", [email])

    if not figures:
        return f'Could not send email to {username} at {email} ({realname}): no figures generated'
    
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
    except Exception as e:
        return f"Could not send email to {username} at {email} ({realname}): {e}"
    return f"Sent mail to {username} at {email} ({realname}) successfully."
