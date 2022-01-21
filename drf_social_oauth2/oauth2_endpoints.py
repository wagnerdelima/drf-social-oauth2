import logging
from json import dumps

from django.http import HttpRequest
from django.utils import timezone
from oauth2_provider.models import get_access_token_model

from oauthlib.common import Request
from oauthlib.oauth2.rfc6749.endpoints.token import TokenEndpoint
from oauthlib.oauth2.rfc6749.tokens import BearerToken
from oauthlib.oauth2.rfc6749.endpoints.base import catch_errors_and_unavailability

from drf_social_oauth2.oauth2_grants import SocialTokenGrant

log = logging.getLogger(__name__)

AccessToken = get_access_token_model()


class SocialTokenServer(TokenEndpoint):
    """
    An endpoint used only for token generation.
    Use this with the KeepRequestCore backend class.
    """

    def __init__(
        self,
        request_validator,
        token_generator=None,
        token_expires_in=None,
        refresh_token_generator=None,
        **kwargs
    ):
        """Construct a client credentials grant server.
        :param request_validator: An implementation of
                                  oauthlib.oauth2.RequestValidator.
        :param token_expires_in: An int or a function to generate a token
                                 expiration offset (in seconds) given a
                                 oauthlib.common.Request object.
        :param token_generator: A function to generate a token from a request.
        :param refresh_token_generator: A function to generate a token from a
                                        request for the refresh token.
        :param kwargs: Extra parameters to pass to authorization-,
                       token-, resource-, and revocation-endpoint constructors.
        """
        self._params = {}
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

    def set_request_object(self, request):
        """This should be called by the KeepRequestCore backend class before
        calling `create_token_response` to store the Django request object.
        """
        if not isinstance(request, HttpRequest):
            raise TypeError("request must be an instance of 'django.http.HttpRequest'")
        self._params['http_request'] = request

    def pop_request_object(self):
        """This is called internaly by `create_token_response`
        to fetch the Django request object and cleanup class instance.
        """
        return self._params.pop('http_request', None)

    # We override this method just so we can pass the django request object
    @catch_errors_and_unavailability
    def create_token_response(
        self, uri, http_method='GET', body=None, headers=None, credentials=None
    ):
        """Extract grant_type and route to the designated handler."""
        request = self.__create_django_request(
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

        # validates request and assigns user to request object.
        SocialTokenGrant(self.request_validator).validate_token_request(request)

        access_token = self.__check_for_no_existing_tokens(request)
        # Checks if the last token created exists, and if so, if token is still valid.
        if access_token is None or (access_token and access_token.is_expired()):
            # create the request again, as a convert_token grant type.
            request = self.__create_django_request(
                uri, http_method, body, headers, credentials
            )
            return grant_type_handler.create_token_response(
                request, self.default_token_type
            )

        # if token is valid, do not create a new token, just return the token.
        token = {
            'access_token': access_token.token,
            'expires_in': (
                access_token.expires - timezone.now()
            ).total_seconds(),
            'scope': access_token.scope,
            'refresh_token': access_token.refresh_token.token,
            'token_type': 'Bearer',
        }
        return headers, dumps(token), 200

    def __check_for_no_existing_tokens(self, request: Request):
        """
        Checks if the last token created.
        """
        return AccessToken.objects.filter(
            user=request.user, application=request.client,
        ).last()

    def __create_django_request(
        self, uri, http_method='GET', body=None, headers=None, credentials=None
    ):
        """
        Assembles a request and assigns django_request to Request object.
        """
        request = Request(uri, http_method=http_method, body=body, headers=headers)
        request.scopes = ['read', 'write']
        request.extra_credentials = credentials
        # Make sure we consume the django request object
        request.django_request = self.pop_request_object()

        return request
