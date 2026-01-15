"""
OAuth2 backend classes for drf-social-oauth2.

This module provides custom OAuth2 backend classes that extend the
django-oauth-toolkit backends to support social authentication.
"""

from typing import Any, Tuple

from django.http import HttpRequest

from oauth2_provider.settings import oauth2_settings

from drf_social_oauth2.oauth2_endpoints import SocialTokenServer


class KeepRequestCore(oauth2_settings.OAUTH2_BACKEND_CLASS):
    """OAuth2 backend that preserves the Django request object.

    Subclass of oauth2_settings.OAUTH2_BACKEND_CLASS that passes the Django
    request object through to the server_class instance.

    This backend should only be used in views with SocialTokenServer
    as the server_class.

    Raises:
        TypeError: If server_class is not an instance of SocialTokenServer.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the backend and validate server_class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            TypeError: If server_class is not an instance of SocialTokenServer.
        """
        super(KeepRequestCore, self).__init__(*args, **kwargs)
        if not isinstance(self.server, SocialTokenServer):
            raise TypeError("server_class must be an instance of 'SocialTokenServer'")

    def create_token_response(
        self, request: HttpRequest
    ) -> Tuple[str, dict, str, int]:
        """Create a token response while preserving the Django request.

        A wrapper method that calls create_token_response on the server_class
        instance after storing the Django request object.

        Args:
            request: The current django.http.HttpRequest object.

        Returns:
            A tuple of (url, headers, body, status).
        """
        self.server.set_request_object(request)
        return super(KeepRequestCore, self).create_token_response(request)
