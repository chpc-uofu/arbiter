import re
import logging
from pwd import getpwnam


USEC_PER_SEC = 1000**2
BYTES_PER_GIB = 1024**3
SEC_PER_MIN = 60
SEC_PER_HOUR = 60**2
SEC_PER_DAY = 60**2 * 24
SEC_PER_WEEK = 60**2 * 24 * 7

logger = logging.getLogger(__name__)



def log_debug(func):
    def f(*args):
        args_str = '('
        for arg in args:
            if isinstance(arg, float):
                args_str += '%.2f' % arg
            elif isinstance(arg, int):
                args_str += '%d' % arg
            elif isinstance(arg, str):
                args_str += '"%s"' % arg
            else:
                args_str += '%s' % arg
            args_str += ', '
        args_str = args_str[:-2] + ')'
        logger.debug(f'{func.__name__}{args_str}')
        return func(*args)
    return f


def strip_port(host: str) -> str:
    return host.split(":")[0]


def get_uid(unit: str) -> int | None:
    match = re.search(r"user-(\d+)\.slice", unit)
    if not match:
        return None
    return int(match.group(1))


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
    return f"{username}@localhost"


def default_realname_lookup(username: str) -> str:
    realname = f"unknown real name"
    try:
        pwd_info = getpwnam(username)
        gecos = pwd_info.pw_gecos
        realname = gecos.rstrip() or realname
    except KeyError:
        pass
    return realname


def sec_to_promtime(seconds: str):
    time_units = [
        (7 * 24 * 3600, 'w'), 
        (24 * 3600, 'd'),
        (3600, 'h'),
        (60, 'm'),
        (1, 's')
    ]
    components = []
    for unit_seconds, label in time_units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            components.append(f"{count}{label}")
            seconds %= unit_seconds
    return ''.join(components) if components else '0s'


def promtime_to_sec(time_str: str) -> int | None:
    total_seconds = 0
    pattern = r'(\d+)([wdhms])'
    matches = re.findall(pattern, time_str)
    if ''.join(f"{amount}{unit}" for amount, unit in matches) != time_str:
        return None
    unit_to_seconds = {
        'w': 7 * 24 * 3600,  # weeks
        'd': 24 * 3600,      # days
        'h': 3600,           # hours
        'm': 60,             # minutes
        's': 1               # seconds
    }
    for amount, unit in matches:
        total_seconds += int(amount) * unit_to_seconds[unit]
    return total_seconds


def cores_to_usec(cores: float) -> int:
    usec = cores * USEC_PER_SEC
    if usec < 1:
        return 1
    return int(usec)

def usec_to_cores(usec: int) -> float:
    return usec / USEC_PER_SEC

def gib_to_bytes(gib: float) -> int:
    _bytes = gib * BYTES_PER_GIB
    return int(_bytes)


def bytes_to_gib(byts: int) -> float:
    return byts / BYTES_PER_GIB
