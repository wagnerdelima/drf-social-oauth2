"""
Social authentication backends for drf-social-oauth2.

This module provides custom social authentication backends for various providers
including Django's own OAuth2 backend, Google Identity, and LinkedIn OpenID.
"""

from typing import Any

from django.urls import reverse_lazy
from social_core.backends.google import GooglePlusAuth
from social_core.backends.linkedin import LinkedinOpenIdConnect
from social_core.backends.oauth import BaseOAuth2

from drf_social_oauth2.settings import (
    DRFSO2_PROPRIETARY_BACKEND_NAME,
    DRFSO2_URL_NAMESPACE,
)

# Google treats @googlemail.com (used in some regions, e.g. Germany, UK) as an
# alias of @gmail.com — the same mailbox is reachable under either domain.
# Without normalization, the same Google account signing in once with each
# domain produces two distinct social UIDs and therefore two Django users.
GOOGLE_MAIL_ALIAS_DOMAIN: str = 'googlemail.com'
GOOGLE_MAIL_CANONICAL_DOMAIN: str = 'gmail.com'


def normalize_google_email_address(email: str | None) -> str | None:
    """Normalize a Google email so gmail/googlemail aliases compare equal.

    Replaces a trailing ``@googlemail.com`` domain (case-insensitive) with
    ``@gmail.com`` while preserving the original local part. Non-Google
    addresses and falsy values are returned unchanged.

    Args:
        email: An email address, or None.

    Returns:
        The normalized email, or the original value if no normalization applies.
    """
    if not email or '@' not in email:
        return email

    local, _, domain = email.rpartition('@')
    if domain.lower() == GOOGLE_MAIL_ALIAS_DOMAIN:
        return f'{local}@{GOOGLE_MAIL_CANONICAL_DOMAIN}'
    return email


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
    # reverse_lazy defers URL resolution until first use so this module can be
    # imported before Django's URL conf has been loaded — eager reverse() here
    # raised NoReverseMatch during test collection (and any early import) when
    # the configured namespace isn't registered yet.
    AUTHORIZATION_URL = reverse_lazy(
        f'{DRFSO2_URL_NAMESPACE}:authorize' if DRFSO2_URL_NAMESPACE else 'authorize'
    )
    ACCESS_TOKEN_URL = reverse_lazy(
        f'{DRFSO2_URL_NAMESPACE}:token' if DRFSO2_URL_NAMESPACE else 'token'
    )


class GoogleIdentityBackend(GooglePlusAuth):
    """Google Identity authentication backend using OpenID Connect.

    Google has shifted to OpenID Connect instead of access tokens.
    This backend enables authentication with Google's id_token.

    Email addresses are normalized so that the @googlemail.com alias maps to
    its canonical @gmail.com form, preventing duplicate Django user accounts
    when the same Google user signs in under both domains.

    Attributes:
        name: The backend identifier name.
    """

    name: str = "google-identity"

    def user_data(
        self, access_token: str, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Fetch user data from Google's tokeninfo endpoint.

        Args:
            access_token: The Google id_token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dictionary containing user information from Google.
        """
        response: dict[str, Any] = self.get_json(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"id_token": access_token},
        )
        self.process_error(response)
        return response

    def get_user_details(self, response: dict[str, Any]) -> dict[str, Any]:
        """Return normalized user details for a Google account.

        Folds the @googlemail.com alias into @gmail.com so the social UID
        (which defaults to email) is stable across both domain forms.

        Args:
            response: The raw response from Google's userinfo/tokeninfo endpoint.

        Returns:
            Dictionary of user details with a normalized email and username.
        """
        details = super().get_user_details(response)
        normalized = normalize_google_email_address(details.get('email'))
        if normalized and normalized != details.get('email'):
            details['email'] = normalized
            details['username'] = normalized.split('@', 1)[0]
        return details


class LinkedInOpenIDUserInfo(LinkedinOpenIdConnect):
    """LinkedIn OpenID Connect authentication backend.

    Fetches user information from LinkedIn's userinfo endpoint.
    """

    def user_data(
        self, access_token: str, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Fetch user data from LinkedIn's userinfo endpoint.

        Args:
            access_token: The LinkedIn access token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dictionary containing user information from LinkedIn.
        """
        response: dict[str, Any] = self.get_json(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.process_error(response)
        return response

    def get_user_details(self, response: dict[str, Any]) -> dict[str, str | None]:
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
