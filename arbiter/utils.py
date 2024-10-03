import logging
import aiohttp
import http
from django.conf import settings

logger = logging.getLogger(__name__)

async def set_property(
    target, session: aiohttp.ClientSession, prop: dict[str, str]
) -> tuple[http.HTTPStatus, str]:
    """
    Sets a systemd property for a unit on host by sending a control request to cgroup-agent.
    A property is a JSON object with the name and value of a property.For example,
    prop = {"name" : "CPUQuotaPerSecUSec, "value", "1000000000"}
    """

    endpoint = f"{settings.ARBITER_WARDEN_PROTOCOL}://{target.host}:{settings.ARBITER_WARDEN_PORT}/control"
    logger.info(f"setting property {prop['name']} with value {prop['value']} for {target.unit} on {endpoint}")
    payload = {"unit": target.unit, "property": prop}
    auth_header = {"Authorization": "Bearer " + settings.ARBITER_CONTROL_KEY}
    try:
        async with session.post(
            url=endpoint, json=payload, timeout=5, headers=auth_header, ssl=False
        ) as response:
            status = response.status
            message = await response.json()
    except (aiohttp.ClientConnectionError, aiohttp.ClientError) as e:
        status = http.HTTPStatus.SERVICE_UNAVAILABLE
        message = f"Service Unavailable : {e}"

    return status, message


def strip_port(host: str) -> str:
    """
    Strips the port from a host string
    """
    return host.split(":")[0]
