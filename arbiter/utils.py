import logging
import aiohttp
import http
from pwd import getpwuid, getpwnam
from arbiter.conf import (
    WARDEN_DISABLE_AUTH,
    WARDEN_DISABLE_SSL,
    WARDEN_DISABLE_TLS,
    WARDEN_PORT,
    WARDEN_BEARER,
    ARBITER_EMAIL_DOMAIN,
)

logger = logging.getLogger(__name__)


async def set_property(
    target, session: aiohttp.ClientSession, prop: dict[str, str]
) -> tuple[http.HTTPStatus, str]:
    """
    Sets a systemd property for a unit on host by sending a control request to cgroup-agent.
    A property is a JSON object with the name and value of a property.For example,
    prop = {"name" : "CPUQuotaPerSecUSec, "value", "1000000000"}
    """

    if WARDEN_DISABLE_TLS:
        endpoint = f"http://{target.host}:{WARDEN_PORT}/control"
    else:
        endpoint = f"https://{target.host}:{WARDEN_PORT}/control"

    logger.info(
        f"setting property {prop['name']} with value {prop['value']} for {target.unit} on {endpoint}"
    )
    payload = {"unit": target.unit, "property": prop}

    if WARDEN_DISABLE_AUTH:
        auth_header = None
    else:
        auth_header = {"Authorization": "Bearer " + WARDEN_BEARER}
    try:
        async with session.post(
            url=endpoint,
            json=payload,
            timeout=5,
            headers=auth_header,
            ssl=WARDEN_DISABLE_SSL,
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


def default_user_lookup(username: str) -> tuple[str, str, str]:
    realname = default_realname_lookup(username=username)
    email = default_email_lookup(username=username)
    return username, realname, email


def default_email_lookup(username: str) -> str:
    return f"{username}@{ARBITER_EMAIL_DOMAIN}"


def default_realname_lookup(username: str) -> str:
    realname = f"unknown real name"
    try:
        pwd_info = getpwnam(username)
        gecos = pwd_info.pw_gecos
        realname = gecos.rstrip() or realname
    except KeyError:
        pass
    return realname
