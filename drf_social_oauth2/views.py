from json import loads as json_loads

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
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
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


class CsrfExemptMixin:
    """
    Exempts the view from CSRF requirements.
    NOTE:
        This should be the left-most mixin of a view.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class TokenView(CsrfExemptMixin, OAuthLibMixin, APIView):
    """
    Implements an endpoint to provide access tokens

    The endpoint is used in the following flows:

    * Authorization code
    * Password
    * Client credentials
    """

    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS
    permission_classes = (AllowAny,)

    def post(self, request: Request, *args, **kwargs):
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
    """
    Implements an endpoint to convert a provider token to an access token

    The endpoint is used in the following flows:

    * Authorization code
    * Client credentials
    """

    server_class = SocialTokenServer
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = KeepRequestCore
    permission_classes = (AllowAny,)

    def post(self, request: Request, *args, **kwargs):
        serializer = ConvertTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Use the rest framework `.data` to fake the post body of the django request.
        request._request.POST = request._request.POST.copy()
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
                {'access_denied': f'The token you provided is invalid or expired.'},
                status=HTTP_400_BAD_REQUEST,
            )

        return Response(data=json_loads(body), status=status)


class RevokeTokenView(CsrfExemptMixin, OAuthLibMixin, APIView):
    """
    Implements an endpoint to revoke access or refresh tokens
    """

    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, *args, **kwargs):
        serializer = RevokeTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Use the rest framework `.data` to fake the post body of the django request.
        request._request.POST = request._request.POST.copy()
        for key, value in serializer.validated_data.items():
            request._request.POST[key] = value

        url, headers, body, status = self.create_revocation_response(request._request)
        return Response(
            data=json_loads(body) if body else '', status=status if body else 204
        )


class InvalidateSessions(APIView):
    """
    Delete all access tokens associated with a client id.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def post(self, request: Request, *args, **kwargs):
        serializer = InvalidateSessionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id = serializer.validated_data['client_id']

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
    """
    Invalidate all refresh tokens associated with a client id.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def post(self, request: Request, *args, **kwargs):
        serializer = InvalidateRefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id = serializer.validated_data['client_id']

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
    """
    An endpoint for disconnect social auth backend providers such as Facebook.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def post(self, request: Request, *args, **kwargs):
        serializer = DisconnectBackendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        backend = serializer.validated_data['backend']
        association_id = serializer.validated_data['association_id']
        strategy = load_strategy(request=request)
        try:
            namespace = 'drf'
            backend = load_backend(
                strategy, backend, reverse(namespace + ":complete", args=(backend,))
            )
        except MissingBackend:
            return Response(
                {"backend": ["Invalid backend."]}, status=HTTP_400_BAD_REQUEST
            )

        backend.disconnect(
            user=self.get_object(), association_id=association_id, *args, **kwargs
        )
        return Response(status=HTTP_204_NO_CONTENT)
