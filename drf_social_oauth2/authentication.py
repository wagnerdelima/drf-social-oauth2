"""
Authentication backends for drf-social-oauth2.

This module provides authentication classes that integrate python-social-auth
with Django REST Framework.
"""

from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, TypeVar

from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from social_django.views import NAMESPACE
from social_django.utils import load_backend, load_strategy
from social_core.exceptions import MissingBackend
from social_core.utils import requests


F = TypeVar('F', bound=Callable[..., Any])


def validator(function: F) -> F:
    """Decorator to validate the Authorization header format.

    Validates that the Authorization header follows the format:
        Bearer <backend> <token>

    Args:
        function: The authenticate method to wrap.

    Returns:
        The wrapped function that validates headers before calling authenticate.

    Raises:
        AuthenticationFailed: When the header format is invalid.
    """
    @wraps(function)
    def wrapper_validation(
        *args: Any, **kwargs: Any
    ) -> Optional[Tuple[AbstractBaseUser, str]]:
        request = args[1]
        auth_header = get_authorization_header(request).decode(HTTP_HEADER_ENCODING)
        auth: List[str] = auth_header.split()

        if not auth or auth[0].lower() != 'bearer':
            return None

        if len(auth) == 1:
            raise AuthenticationFailed('Invalid token header. No backend provided.')
        elif len(auth) == 2:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth) > 3:
            raise AuthenticationFailed(
                'Invalid token header. Token string should not contain spaces.'
            )

        return function(*args, backend=auth[1], token=auth[2], **kwargs)

    return wrapper_validation  # type: ignore[return-value]


class SocialAuthentication(BaseAuthentication):
    """Authentication backend using python-social-auth.

    Clients authenticate by passing a token in the Authorization header:
        Authorization: Bearer <backend> <token>

    Example:
        Authorization: Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a

    Attributes:
        www_authenticate_realm: The realm name for WWW-Authenticate header.

    Raises:
        AuthenticationFailed: When token is invalid, backend is missing,
            or credentials are malformed.
    """

    www_authenticate_realm: str = 'api'

    @validator
    def authenticate(
        self, request: Request, **kwargs: Any
    ) -> Optional[Tuple[AbstractBaseUser, str]]:
        """Authenticate the request using a social provider token.

        Args:
            request: The DRF request object.
            **kwargs: Must contain 'token' and 'backend' keys (injected by validator).

        Returns:
            A tuple of (user, token) if authentication succeeds, None otherwise.

        Raises:
            AuthenticationFailed: When authentication fails.
        """
        token: str = kwargs['token']
        backend_name: str = kwargs['backend']
        strategy = load_strategy(request=request)

        try:
            backend = load_backend(
                strategy,
                backend_name,
                reverse(f"{NAMESPACE}:complete", args=(backend_name,)),
            )
            user = backend.do_auth(access_token=token)
        except MissingBackend:
            raise AuthenticationFailed('Invalid token header. Invalid backend.')
        except requests.HTTPError as e:
            raise AuthenticationFailed(e.response.text)

        if not user:
            raise AuthenticationFailed('Bad credentials')
        return user, token

    def authenticate_header(self, request: Request) -> str:
        """Return the WWW-Authenticate header value.

        Args:
            request: The DRF request object.

        Returns:
            The WWW-Authenticate header value for Bearer authentication.
        """
        return f'Bearer backend realm="{self.www_authenticate_realm}"'
