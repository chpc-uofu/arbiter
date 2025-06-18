#!/usr/bin/env python
"""Basic backend configuration for OIDC support."""
import logging
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

logger = logging.getLogger(__name__)


class OIDCBackend(OIDCAuthenticationBackend):

    def update_user(self, user, claims):
        user = super().update_user(user, claims)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        logger.debug(f'Created user {user} with claims {claims} by OICD')
        return user
