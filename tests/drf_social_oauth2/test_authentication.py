import pytest
from rest_framework.exceptions import AuthenticationFailed

from drf_social_oauth2.authentication import SocialAuthentication
from django.http.request import HttpRequest


def create_request(content: str = 'Bearer'):
    request = HttpRequest()
    request.META = {
        'HTTP_AUTHORIZATION': content
    }
    return request


def test_authenticate_no_auth_header_fail():
    authenticated = SocialAuthentication()
    assert not authenticated.authenticate(HttpRequest())


def test_authenticate_no_backend_fail():
    request = create_request('Bearer')
    authenticated = SocialAuthentication()

    with pytest.raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_empty_bearer_fail():
    request = create_request('Bearer facebook')
    authenticated = SocialAuthentication()

    with pytest.raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_wrongly_formatted_token_fail():
    token = 'Bearer facebook 401f7ac837da42b9 7f613d789819ff93537bee6a'
    request = create_request(token)
    authenticated = SocialAuthentication()

    with pytest.raises(AuthenticationFailed):
        authenticated.authenticate(request)
