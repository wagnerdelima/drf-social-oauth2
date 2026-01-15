"""
Social authentication backends for drf-social-oauth2.

This module provides custom social authentication backends for various providers
including Django's own OAuth2 backend, Google Identity, and LinkedIn OpenID.
"""

from typing import Any, Dict, Optional

from django.urls import reverse

from social_core.backends.oauth import BaseOAuth2
from social_core.backends.google import GooglePlusAuth
from social_core.backends.linkedin import LinkedinOpenIdConnect

from drf_social_oauth2.settings import (
    DRFSO2_PROPRIETARY_BACKEND_NAME,
    DRFSO2_URL_NAMESPACE,
)


class DjangoOAuth2(BaseOAuth2):
    """Default OAuth2 authentication backend used by this package.

    This backend allows authentication against the Django application's
    own OAuth2 endpoints.

    Attributes:
        name: The backend identifier name.
        AUTHORIZATION_URL: The URL for OAuth2 authorization.
        ACCESS_TOKEN_URL: The URL for obtaining access tokens.
    """

    name: str = DRFSO2_PROPRIETARY_BACKEND_NAME
    AUTHORIZATION_URL: str = reverse(
        f'{DRFSO2_URL_NAMESPACE}:authorize' if DRFSO2_URL_NAMESPACE else 'authorize'
    )
    ACCESS_TOKEN_URL: str = reverse(
        f'{DRFSO2_URL_NAMESPACE}:token' if DRFSO2_URL_NAMESPACE else 'token'
    )


class GoogleIdentityBackend(GooglePlusAuth):
    """Google Identity authentication backend using OpenID Connect.

    Google has shifted to OpenID Connect instead of access tokens.
    This backend enables authentication with Google's id_token.

    Attributes:
        name: The backend identifier name.
    """

    name: str = "google-identity"

    def user_data(
        self, access_token: str, *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        """Fetch user data from Google's tokeninfo endpoint.

        Args:
            access_token: The Google id_token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dictionary containing user information from Google.
        """
        response: Dict[str, Any] = self.get_json(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"id_token": access_token},
        )
        self.process_error(response)
        return response


class LinkedInOpenIDUserInfo(LinkedinOpenIdConnect):
    """LinkedIn OpenID Connect authentication backend.

    Fetches user information from LinkedIn's userinfo endpoint.
    """

    def user_data(
        self, access_token: str, *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        """Fetch user data from LinkedIn's userinfo endpoint.

        Args:
            access_token: The LinkedIn access token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dictionary containing user information from LinkedIn.
        """
        response: Dict[str, Any] = self.get_json(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.process_error(response)
        return response

    def get_user_details(self, response: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract user details from the LinkedIn response.

        Args:
            response: The response dictionary from LinkedIn's userinfo endpoint.

        Returns:
            Dictionary containing normalized user details.
        """
        username_key: str = self.setting("USERNAME_KEY", self.USERNAME_KEY)
        return {
            "username": response.get(username_key),
            "email": response.get("email"),
            "fullname": response.get("name"),
            "first_name": response.get("given_name"),
            "last_name": response.get("family_name"),
            "picture": response.get("picture"),
        }
