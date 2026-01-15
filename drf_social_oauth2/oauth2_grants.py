"""
OAuth2 grant types for drf-social-oauth2.

This module provides custom OAuth2 grant types that support
social authentication token conversion.
"""

from logging import getLogger

from django.urls import reverse

from oauthlib.common import Request
from oauthlib.oauth2.rfc6749 import errors
from oauthlib.oauth2.rfc6749.grant_types.refresh_token import RefreshTokenGrant

from social_django.views import NAMESPACE
from social_django.utils import load_backend, load_strategy
from social_core.exceptions import MissingBackend, SocialAuthBaseException
from social_core.utils import requests

from drf_social_oauth2.settings import DRFSO2_URL_NAMESPACE


log = getLogger(__name__)


class SocialTokenGrant(RefreshTokenGrant):
    """OAuth2 grant type for converting social provider tokens.

    This grant type handles the 'convert_token' grant which converts
    a social provider access token into an OAuth2 access token.

    See Also:
        RFC 6749 Section 6: https://tools.ietf.org/html/rfc6749#section-6
    """

    def validate_token_request(self, request: Request) -> None:
        """Validate the token conversion request.

        Validates that the request contains all required parameters and
        authenticates the user via the specified social backend.

        Args:
            request: The oauthlib Request object containing:
                - grant_type: Must be 'convert_token'
                - token: The social provider access token
                - backend: The social backend name (e.g., 'facebook')
                - client_id: The OAuth2 application client ID

        Raises:
            UnsupportedGrantTypeError: If grant_type is not 'convert_token'.
            InvalidRequestError: If token or backend parameters are missing,
                or if the backend is invalid.
            MissingClientIdError: If client_id is not provided.
            InvalidClientIdError: If client_id is invalid.
            InvalidClientError: If client authentication fails.
            InvalidGrantError: If user credentials are invalid or user is inactive.
            AccessDeniedError: If social authentication fails.
        """
        # Set defaults to avoid AttributeError later
        request._params.setdefault("backend", None)
        request._params.setdefault("client_secret", None)

        if request.grant_type != 'convert_token':
            raise errors.UnsupportedGrantTypeError(request=request)

        # Validate token parameter (social provider token)
        if request.token is None:
            raise errors.InvalidRequestError(
                description='Missing token parameter.', request=request
            )

        # Validate backend parameter (social backend name)
        if request.backend is None:
            raise errors.InvalidRequestError(
                description='Missing backend parameter.', request=request
            )

        if not request.client_id:
            raise errors.MissingClientIdError(request=request)

        if not self.request_validator.validate_client_id(request.client_id, request):
            raise errors.InvalidClientIdError(request=request)

        # Authenticate the client
        if self.request_validator.client_authentication_required(request):
            log.debug('Authenticating client, %r.', request)
            if not self.request_validator.authenticate_client(request):
                log.debug('Invalid client (%r), denying access.', request)
                raise errors.InvalidClientError(request=request)
        elif not self.request_validator.authenticate_client_id(
            request.client_id, request
        ):
            log.debug('Client authentication failed, %r.', request)
            raise errors.InvalidClientError(request=request)

        # Use refresh_token grant type for validation as it's the most
        # permissive and logical grant for our needs
        request.grant_type = "refresh_token"
        self.validate_grant_type(request)

        self.validate_scopes(request)

        # Load the social authentication strategy and backend
        strategy = load_strategy(request=request.django_request)

        try:
            backend = load_backend(
                strategy,
                request.backend,
                reverse(
                    f"{DRFSO2_URL_NAMESPACE}:{NAMESPACE}:complete",
                    args=(request.backend,),
                ),
            )
        except MissingBackend:
            raise errors.InvalidRequestError(
                description='Invalid backend parameter.', request=request
            )

        # Authenticate with the social backend
        try:
            user = backend.do_auth(access_token=request.token)
        except requests.HTTPError as e:
            raise errors.InvalidRequestError(
                description=f"Backend responded with HTTP{e.response.status_code}: {e.response.text}.",
                request=request,
            )
        except SocialAuthBaseException as e:
            raise errors.AccessDeniedError(description=str(e), request=request)

        if not user:
            raise errors.InvalidGrantError(
                'Invalid credentials given.', request=request
            )

        if not user.is_active:
            raise errors.InvalidGrantError('User inactive or deleted.', request=request)

        request.user = user
        log.debug('Authorizing access to user %r.', request.user)
