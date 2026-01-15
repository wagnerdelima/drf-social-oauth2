"""
Views for drf-social-oauth2.

This module provides API views for OAuth2 token operations including:
- Token generation and conversion from social providers
- Token revocation
- Session invalidation
- Backend disconnection
"""

import logging
from json import loads as json_loads
from typing import Any, Dict, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from social_core.exceptions import MissingBackend
from social_django.utils import load_strategy, load_backend

from oauth2_provider.models import Application, AccessToken, RefreshToken
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views.mixins import OAuthLibMixin
from oauthlib.oauth2.rfc6749.errors import (
    InvalidClientError,
    UnsupportedGrantTypeError,
    AccessDeniedError,
    MissingClientIdError,
    InvalidRequestError,
)

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.status import (
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from drf_social_oauth2.serializers import (
    InvalidateRefreshTokenSerializer,
    ConvertTokenSerializer,
    RevokeTokenSerializer,
    DisconnectBackendSerializer,
    InvalidateSessionsSerializer,
)
from drf_social_oauth2.oauth2_backends import KeepRequestCore
from drf_social_oauth2.oauth2_endpoints import SocialTokenServer


logger = logging.getLogger(__package__)


def get_application(validated_data: Dict[str, Any]) -> Optional[Application]:
    """Retrieve an Application object based on the provided client_id.

    Args:
        validated_data: A dictionary containing the request validated data,
            expected to contain a 'client_id' key.

    Returns:
        The Application object if found, None otherwise.
    """
    client_id: Optional[str] = validated_data.get('client_id')

    if not client_id:
        return None

    try:
        application = Application.objects.get(client_id=client_id)
    except Application.DoesNotExist:
        return None
    return application


class CsrfExemptMixin:
    """Mixin that exempts the view from CSRF requirements.

    Note:
        This should be the left-most mixin of a view to ensure proper
        method resolution order (MRO).
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args: Any, **kwargs: Any) -> Response:
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class TokenView(CsrfExemptMixin, OAuthLibMixin, APIView):
    """Endpoint to provide access tokens.

    The endpoint is used in the following OAuth2 flows:
        - Authorization code
        - Password
        - Client credentials
    """

    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS
    permission_classes = (AllowAny,)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle POST request to generate access tokens.

        Args:
            request: The DRF request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response containing the access token or error details.
        """
        # Use the rest framework `.data` to fake the post body of the django request.
        mutable_data = request.data.copy()
        request._request.POST = request._request.POST.copy()
        for key, value in mutable_data.items():
            request._request.POST[key] = value

        try:
            url, headers, body, status = self.create_token_response(request._request)
        except AccessToken.DoesNotExist:
            return Response(
                data={
                    'invalid_grant': 'The access token of your Refresh Token does not exist.'
                },
                status=HTTP_400_BAD_REQUEST,
            )

        return Response(data=json_loads(body), status=status)


class ConvertTokenView(CsrfExemptMixin, OAuthLibMixin, APIView):
    """Endpoint to convert a social provider token to an OAuth2 access token.

    This view handles the conversion of tokens from social authentication
    providers (e.g., Facebook, Google) into OAuth2 access tokens that can
    be used with this application.
    """

    server_class = SocialTokenServer
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = KeepRequestCore
    permission_classes = (AllowAny,)

    def get_user(self, access_token: str) -> Optional[AbstractBaseUser]:
        """Retrieve the user associated with an access token.

        Args:
            access_token: The access token string.

        Returns:
            The user object if found, None otherwise.
        """
        token = AccessToken.objects.filter(token=access_token).first()
        return token.user if token else None

    def prepare_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add user information to the response data.

        Args:
            data: The response data dictionary.

        Returns:
            The response data with user information added if available.
        """
        user = self.get_user(data.get('access_token'))
        if user:
            data['user'] = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        return data

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle POST request to convert a social provider token.

        Args:
            request: The DRF request object containing grant_type, backend,
                client_id, and token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response containing the OAuth2 access token or error details.
        """
        if 'client_secret' in request.data:
            logger.warning(
                'client_secret is present in the request data. '
                'Consider removing it for better security.'
            )
        serializer = ConvertTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = get_application(serializer.validated_data)
        if not application:
            return Response(
                {"detail": "The application for this client_id does not exist."},
                status=HTTP_400_BAD_REQUEST,
            )
        # Use the rest framework `.data` to fake the post body of the django request.
        request._request.POST = request._request.POST.copy()
        request._request.POST['client_secret'] = application.client_secret
        for key, value in serializer.validated_data.items():
            request._request.POST[key] = value

        try:
            url, headers, body, status = self.create_token_response(request._request)
        except InvalidClientError:
            return Response(
                data={'invalid_client': 'Missing client type.'},
                status=HTTP_400_BAD_REQUEST,
            )
        except MissingClientIdError as ex:
            return Response(
                data={'invalid_request': ex.description},
                status=HTTP_400_BAD_REQUEST,
            )
        except InvalidRequestError as ex:
            return Response(
                data={'invalid_request': ex.description},
                status=HTTP_400_BAD_REQUEST,
            )
        except UnsupportedGrantTypeError:
            return Response(
                data={'unsupported_grant_type': 'Missing grant type.'},
                status=HTTP_400_BAD_REQUEST,
            )
        except AccessDeniedError:
            return Response(
                {'access_denied': 'The token you provided is invalid or expired.'},
                status=HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as e:
            if 'email' in str(e) and 'already exists' in str(e):
                return Response(
                    {'error': 'A user with this email already exists.'},
                    status=HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {'error': 'Database error.'},
                    status=HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            logger.exception('Unexpected error during token conversion')
            return Response(
                {'error': 'An unexpected error occurred.'},
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = self.prepare_response(json_loads(body))
        return Response(data, status=status)


class RevokeTokenView(CsrfExemptMixin, OAuthLibMixin, APIView):
    """Endpoint to revoke access or refresh tokens.

    Requires authentication. The token to revoke is extracted from the
    Authorization header.
    """

    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle POST request to revoke a token.

        Args:
            request: The DRF request object containing client_id.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response with 204 status on success or error details.
        """
        if 'client_secret' in request.data:
            logger.warning(
                'client_secret is present in the request data. '
                'Consider removing it for better security.'
            )

        auth_header: str = request.META.get('HTTP_AUTHORIZATION', "")
        auth_header = auth_header.replace('Bearer ', '', 1)
        serializer = RevokeTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = get_application(serializer.validated_data)
        if not application:
            return Response(
                {"detail": "The application for this client_id does not exist."},
                status=HTTP_400_BAD_REQUEST,
            )

        # Use the rest framework `.data` to fake the post body of the django request.
        request._request.POST = request._request.POST.copy()
        request._request.POST['client_secret'] = application.client_secret
        request._request.POST['token'] = auth_header
        for key, value in serializer.validated_data.items():
            request._request.POST[key] = value

        url, headers, body, status = self.create_revocation_response(request._request)
        return Response(
            data=json_loads(body) if body else '', status=status if body else 204
        )


class InvalidateSessions(APIView):
    """Endpoint to delete all access tokens associated with a client id.

    Requires authentication. Deletes all access tokens for the authenticated
    user and the specified application.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self) -> AbstractBaseUser:
        """Get the authenticated user.

        Returns:
            The authenticated user object.
        """
        return self.request.user

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle POST request to invalidate all sessions.

        Args:
            request: The DRF request object containing client_id.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response with 204 status on success or error details.
        """
        serializer = InvalidateSessionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id: str = serializer.validated_data['client_id']

        try:
            app = Application.objects.get(client_id=client_id)
            AccessToken.objects.filter(user=self.get_object(), application=app).delete()
        except Application.DoesNotExist:
            return Response(
                {
                    "detail": "The application linked to the provided client_id could not be found."
                },
                status=HTTP_400_BAD_REQUEST,
            )

        return Response({}, status=HTTP_204_NO_CONTENT)


class InvalidateRefreshTokens(APIView):
    """Endpoint to invalidate all refresh tokens associated with a client id.

    Requires authentication. Deletes all refresh tokens for the authenticated
    user and the specified application.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self) -> AbstractBaseUser:
        """Get the authenticated user.

        Returns:
            The authenticated user object.
        """
        return self.request.user

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle POST request to invalidate all refresh tokens.

        Args:
            request: The DRF request object containing client_id.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response with 204 status on success or error details.
        """
        serializer = InvalidateRefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id: str = serializer.validated_data['client_id']

        try:
            app = Application.objects.get(client_id=client_id)
            RefreshToken.objects.filter(
                user=self.get_object(), application=app
            ).delete()
        except Application.DoesNotExist:
            return Response(
                {
                    "detail": "The application linked to the provided client_id could not be found."
                },
                status=HTTP_400_BAD_REQUEST,
            )
        return Response({}, HTTP_204_NO_CONTENT)


class DisconnectBackendView(APIView):
    """Endpoint to disconnect social auth backend providers.

    Requires authentication. Disconnects a social authentication provider
    (e.g., Facebook, Google) from the authenticated user's account.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self) -> AbstractBaseUser:
        """Get the authenticated user.

        Returns:
            The authenticated user object.
        """
        return self.request.user

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle POST request to disconnect a social backend.

        Args:
            request: The DRF request object containing backend and association_id.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response with 204 status on success or error details.
        """
        serializer = DisconnectBackendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        backend_name: str = serializer.validated_data['backend']
        association_id: int = serializer.validated_data['association_id']
        strategy = load_strategy(request=request)
        try:
            namespace = 'drf'
            backend = load_backend(
                strategy, backend_name, reverse(namespace + ":complete", args=(backend_name,))
            )
        except MissingBackend:
            return Response(
                {"backend": ["Invalid backend."]}, status=HTTP_400_BAD_REQUEST
            )

        backend.disconnect(
            user=self.get_object(), association_id=association_id, *args, **kwargs
        )
        return Response(status=HTTP_204_NO_CONTENT)
