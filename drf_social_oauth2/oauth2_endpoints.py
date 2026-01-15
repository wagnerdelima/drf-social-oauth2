"""
OAuth2 endpoint classes for drf-social-oauth2.

This module provides custom OAuth2 token endpoints that support
social authentication token conversion.
"""

import logging
from typing import Any, Callable, Dict, Optional, Tuple

from django.http import HttpRequest

from oauthlib.common import Request
from oauthlib.oauth2.rfc6749.endpoints.token import TokenEndpoint
from oauthlib.oauth2.rfc6749.tokens import BearerToken
from oauthlib.oauth2.rfc6749.endpoints.base import catch_errors_and_unavailability

from drf_social_oauth2.oauth2_grants import SocialTokenGrant

log = logging.getLogger(__name__)


class SocialTokenServer(TokenEndpoint):
    """OAuth2 token endpoint for social authentication token conversion.

    This endpoint handles the conversion of social provider tokens to
    OAuth2 access tokens. Use this with the KeepRequestCore backend class.

    Attributes:
        _params: Internal dictionary for storing request parameters.
        request_validator: The OAuth2 request validator instance.
    """

    def __init__(
        self,
        request_validator: Any,
        token_generator: Optional[Callable[..., str]] = None,
        token_expires_in: Optional[int] = None,
        refresh_token_generator: Optional[Callable[..., str]] = None,
        **kwargs: Any
    ) -> None:
        """Construct a social token server.

        Args:
            request_validator: An implementation of oauthlib.oauth2.RequestValidator.
            token_generator: A function to generate a token from a request.
            token_expires_in: An int or a function to generate a token
                expiration offset (in seconds) given an oauthlib.common.Request.
            refresh_token_generator: A function to generate a refresh token.
            **kwargs: Extra parameters passed to endpoint constructors.
        """
        self._params: Dict[str, Any] = {}
        self.request_validator = request_validator
        refresh_grant = SocialTokenGrant(request_validator)
        bearer = BearerToken(
            request_validator,
            token_generator,
            token_expires_in,
            refresh_token_generator,
        )
        TokenEndpoint.__init__(
            self,
            default_grant_type='convert_token',
            grant_types={'convert_token': refresh_grant},
            default_token_type=bearer,
        )

    def set_request_object(self, request: HttpRequest) -> None:
        """Store the Django request object for later use.

        This should be called by the KeepRequestCore backend class before
        calling create_token_response.

        Args:
            request: The Django HttpRequest object.

        Raises:
            TypeError: If request is not a Django HttpRequest instance.
        """
        if not isinstance(request, HttpRequest):
            raise TypeError("request must be an instance of 'django.http.HttpRequest'")
        self._params['http_request'] = request

    def pop_request_object(self) -> Optional[HttpRequest]:
        """Retrieve and remove the stored Django request object.

        This is called internally by create_token_response to fetch the
        Django request object and clean up the class instance.

        Returns:
            The stored HttpRequest object, or None if not set.
        """
        return self._params.pop('http_request', None)

    @catch_errors_and_unavailability
    def create_token_response(
        self,
        uri: str,
        http_method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, str], str, int]:
        """Create a token response for the given request.

        Extracts the grant_type and routes to the designated handler.

        Args:
            uri: The request URI.
            http_method: The HTTP method (default: 'GET').
            body: The request body.
            headers: The request headers.
            credentials: Extra credentials to pass to the grant handler.

        Returns:
            A tuple of (headers, body, status).
        """
        request = self._create_django_request(
            uri, http_method, body, headers, credentials
        )
        grant_type_handler = self.grant_types.get(
            request.grant_type, self.default_grant_type_handler
        )
        log.debug(
            'Dispatching grant_type %s request to %r.',
            request.grant_type,
            grant_type_handler,
        )
        return grant_type_handler.create_token_response(
            request, self.default_token_type
        )

    def _create_django_request(
        self,
        uri: str,
        http_method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Request:
        """Assemble an oauthlib Request with the Django request attached.

        Args:
            uri: The request URI.
            http_method: The HTTP method (default: 'GET').
            body: The request body.
            headers: The request headers.
            credentials: Extra credentials.

        Returns:
            An oauthlib Request object with django_request attribute set.
        """
        request = Request(uri, http_method=http_method, body=body, headers=headers)
        request.scopes = ['read', 'write']
        request.extra_credentials = credentials
        # Make sure we consume the django request object
        request.django_request = self.pop_request_object()

        return request
