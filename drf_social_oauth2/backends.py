try:
    from django.urls import reverse
except ImportError:  # Will be removed in Django 2.0
    from django.core.urlresolvers import reverse

from social_core.backends.oauth import BaseOAuth2
from social_core.backends.google import GooglePlusAuth

from drf_social_oauth2.settings import (
    DRFSO2_PROPRIETARY_BACKEND_NAME,
    DRFSO2_URL_NAMESPACE,
)


class DjangoOAuth2(BaseOAuth2):
    """Default OAuth2 authentication backend used by this package"""

    name = DRFSO2_PROPRIETARY_BACKEND_NAME
    AUTHORIZATION_URL = reverse(
        f'{DRFSO2_URL_NAMESPACE}:authorize' if DRFSO2_URL_NAMESPACE else 'authorize'
    )
    ACCESS_TOKEN_URL = reverse(
        f'{DRFSO2_URL_NAMESPACE}:token' if DRFSO2_URL_NAMESPACE else 'token'
    )


class GoogleIdentityBackend(GooglePlusAuth):
    """
    Google has shifted to Open ID instead of access token. This authentication backend makes it possible to
    authenticate with google id_token.
    """

    name = "google-identity"

    def user_data(self, access_token, *args, **kwargs):
        response = self.get_json(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"id_token": access_token},
        )
        self.process_error(response)
        return response
