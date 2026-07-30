"""
Social authentication backends for drf-social-oauth2.

This module provides custom social authentication backends for various providers
including Django's own OAuth2 backend, Google Identity, and LinkedIn OpenID.
"""

from logging import getLogger
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy
from social_core.backends.google import GoogleOAuth2
from social_core.backends.linkedin import LinkedinOpenIdConnect
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthTokenError

from drf_social_oauth2.settings import (
    DRFSO2_PROPRIETARY_BACKEND_NAME,
    DRFSO2_URL_NAMESPACE,
)

log = getLogger(__name__)

# Google treats @googlemail.com (used in some regions, e.g. Germany, UK) as an
# alias of @gmail.com — the same mailbox is reachable under either domain.
# Without normalization, the same Google account signing in once with each
# domain produces two distinct social UIDs and therefore two Django users.
GOOGLE_MAIL_ALIAS_DOMAIN: str = 'googlemail.com'
GOOGLE_MAIL_CANONICAL_DOMAIN: str = 'gmail.com'


def claim_is_true(value: Any) -> bool:
    """Interpret a Google ID token boolean claim.

    Google's tokeninfo endpoint has returned boolean claims both as JSON
    booleans and as the strings ``"true"``/``"false"`` depending on the
    endpoint version, so both spellings are accepted. Anything else — including
    a missing claim — is treated as false.

    Args:
        value: The raw claim value from the tokeninfo response.

    Returns:
        True only if the claim positively asserts truth.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == 'true'
    return False


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


class GoogleIdentityBackend(GoogleOAuth2):
    """Google Identity authentication backend using OpenID Connect.

    Google has shifted to OpenID Connect instead of access tokens.
    This backend enables authentication with Google's id_token.

    ID tokens are validated against this application's own Google OAuth client
    ID before their claims are trusted — see :meth:`validate_id_token_claims`.

    Email addresses are normalized so that the @googlemail.com alias maps to
    its canonical @gmail.com form, preventing duplicate Django user accounts
    when the same Google user signs in under both domains.

    Attributes:
        name: The backend identifier name.
        TOKENINFO_URL: Google's ID token introspection endpoint.
        VALID_ISSUERS: Issuer claims Google mints ID tokens with.
    """

    name: str = "google-identity"

    TOKENINFO_URL: str = "https://www.googleapis.com/oauth2/v3/tokeninfo"

    # Google issues ID tokens with either spelling of the issuer claim.
    VALID_ISSUERS: frozenset[str] = frozenset(
        {'accounts.google.com', 'https://accounts.google.com'}
    )

    def get_allowed_audiences(self) -> list[str]:
        """Return the Google OAuth client IDs this application accepts tokens for.

        Resolved from the first of these that is set:

        1. ``SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE`` — a single client ID or a
           list of them, for deployments with separate web/iOS/Android clients.
        2. ``SOCIAL_AUTH_GOOGLE_IDENTITY_KEY`` — python-social-auth's
           per-backend convention for this backend's name.
        3. ``SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`` — what releases up to 3.4.1
           instructed users to configure for this backend.

        Returns:
            A non-empty list of accepted audience values.

        Raises:
            ImproperlyConfigured: If no audience is configured. Failing here is
                deliberate: without a known client ID there is nothing to
                validate the token's ``aud`` claim against, and accepting the
                token anyway is the authentication bypass this check exists to
                prevent.
        """
        configured: Any = (
            self.setting('AUDIENCE')
            or self.setting('KEY')
            or self.strategy.setting('GOOGLE_OAUTH2_KEY')
        )

        if isinstance(configured, str):
            configured = [configured]

        audiences = [
            str(audience).strip()
            for audience in configured or []
            if audience and str(audience).strip()
        ]

        if not audiences:
            raise ImproperlyConfigured(
                'The google-identity backend cannot validate Google ID tokens '
                'because no Google OAuth client ID is configured. Set '
                'SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE to your application\'s '
                'Google OAuth client ID (or a list of them). Without it, an ID '
                'token minted for any other Google OAuth client would be '
                'accepted as proof of identity.'
            )

        return audiences

    def validate_id_token_claims(self, response: dict[str, Any]) -> None:
        """Verify a tokeninfo response was really issued to this application.

        Google's tokeninfo endpoint only attests that a token is validly signed
        and unexpired — it cannot know which application is asking, so it does
        not check that the token was minted for *this* application. That check
        is the relying party's responsibility. Skipping it means any ID token
        for any Google OAuth client (including one the attacker registered)
        authenticates its subject here, since the social UID is derived from the
        token's email address.

        Args:
            response: The decoded claims from Google's tokeninfo endpoint.

        Raises:
            AuthTokenError: If the token was issued for a different OAuth
                client, came from an unexpected issuer, or carries an
                unverified email address.
        """
        allowed_audiences = self.get_allowed_audiences()

        raw_audience = response.get('aud')
        if isinstance(raw_audience, (list, tuple, set, frozenset)):
            presented = {str(item) for item in raw_audience if item}
        elif raw_audience:
            presented = {str(raw_audience)}
        else:
            presented = set()

        if not presented:
            raise AuthTokenError(
                self, 'Google ID token is missing the "aud" claim.'
            )

        if presented.isdisjoint(allowed_audiences):
            # The presented audience is attacker-supplied; the configured one is
            # not echoed back to the client.
            log.warning(
                'Rejected a Google ID token issued for audience(s) %s; this '
                'application accepts %s.',
                sorted(presented),
                sorted(allowed_audiences),
            )
            raise AuthTokenError(
                self,
                'Google ID token was issued for a different OAuth client.',
            )

        issuer = response.get('iss')
        if issuer not in self.VALID_ISSUERS:
            raise AuthTokenError(
                self, f'Google ID token has an unexpected issuer: {issuer!r}.'
            )

        # The social UID defaults to the email address, so an unverified email
        # would let a token holder claim a mailbox they do not control.
        if not claim_is_true(response.get('email_verified')):
            raise AuthTokenError(
                self, 'Google ID token carries an unverified email address.'
            )

    def user_data(
        self, access_token: str, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Fetch and validate user data from Google's tokeninfo endpoint.

        Args:
            access_token: The Google id_token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dictionary containing user information from Google.

        Raises:
            AuthTokenError: If the token's claims do not identify it as having
                been issued to this application.
        """
        response: dict[str, Any] = self.get_json(
            self.TOKENINFO_URL,
            params={"id_token": access_token},
        )
        self.process_error(response)
        self.validate_id_token_claims(response)
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
