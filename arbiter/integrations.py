from arbiter.models import Target
from typing import NamedTuple
from pwd import getpwuid, getpwnam
from django.conf import settings


class UserInfo(NamedTuple):
    username: str
    realname: str
    email: str


def arbiter_user_lookup(target : "Target") -> UserInfo | None:
    """Looks up a user's information given the target."""

    username = username_lookup(uid=target.uid)
    realname = realname_lookup(username=username)
    email = email_lookup(username=username)
    return UserInfo(username, realname, email)


# your custom username lookup goes here
def username_lookup(uid : int) -> str:
    """Returns the username associated with the give UID."""
    return _default_username_lookup(uid)


# your custom email lookup goes here.
def email_lookup(username : str) -> str:
    """Returns the email address of a user given the username."""
    return _default_email_lookup(username)


# your custom user lookup goes here. 
def realname_lookup(username: str) -> str:
    """
    Returns the realname of a user given the username.
    """

    return _default_realname_lookup(username=username)


# your custom uid lookup goes here.
def uid_lookup(username: str) -> str:
    """Returns the UID of associated with the given username."""
    return _default_uid_lookup(username=username)


def _default_username_lookup(uid: int) -> str:
    """
    The default username resolution method.
    Assumes that UID on target and this 
    machine are consistent. 
    """

    username = f"unknown username"
    try:
        pwd_info = getpwuid(uid)
        usr = pwd_info.pw_name
        username = usr.rstrip() or username
    except KeyError:
        pass
    return username


def _default_email_lookup(username: str) -> str:
    return f"{username}@{settings.ARBITER_EMAIL_DOMAIN}"


def _default_realname_lookup(username: str) -> str:
    realname = f"unknown real name"
    try:
        pwd_info = getpwnam(username)
        gecos = pwd_info.pw_gecos
        realname = gecos.rstrip() or realname
    except KeyError:
        pass
    return realname


def _default_uid_lookup(username: str) -> int:
    uid = -1
    try:
        pwd_info = getpwnam(username)
        gecos = pwd_info.pw_uid
        uid = int(gecos.rstrip()) or uid
    except KeyError:
        pass
    return uid