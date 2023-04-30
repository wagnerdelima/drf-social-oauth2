import os

from rest_framework.exceptions import AuthenticationFailed
from pytest import raises

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf_social_oauth2.test_settings')

from django.http.request import HttpRequest
from django import setup

setup()

from drf_social_oauth2.authentication import SocialAuthentication


def create_request(content: str = 'Bearer'):
    request = HttpRequest()
    request.META = {'HTTP_AUTHORIZATION': content}
    request.session = None
    return request


def test_authenticate_no_auth_header_fail():
    authenticated = SocialAuthentication()
    assert not authenticated.authenticate(HttpRequest())


def test_authenticate_no_backend_fail():
    request = create_request('JWT')
    authenticated = SocialAuthentication()

    assert not authenticated.authenticate(request)


def test_authenticate_no_bearer_token_type():
    request = create_request('Bearer')
    authenticated = SocialAuthentication()

    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_empty_bearer_fail():
    request = create_request('Bearer facebook')
    authenticated = SocialAuthentication()

    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_wrongly_formatted_token_fail():
    token = 'Bearer facebook 401f7ac837da42b9 7f613d789819ff93537bee6a'
    request = create_request(token)
    authenticated = SocialAuthentication()

    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate(mocker):
    token = 'Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a'

    request = mocker.patch('django.http.request.HttpRequest')
    request.session = None
    request.META = {'HTTP_AUTHORIZATION': token}

    mocker.patch('drf_social_oauth2.authentication.load_backend')
    authenticated = SocialAuthentication()
    user, token = authenticated.authenticate(request)
    assert user
    assert token == '401f7ac837da42b97f613d789819ff93537bee6a'


def test_authenticate_missing_backend():
    token = 'Bearer unknown 401f7ac837da42b97f613d789819ff93537bee6a'
    request = create_request(token)

    authenticated = SocialAuthentication()
    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_user_not_found(mocker):
    token = 'Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a'

    request = mocker.patch('django.http.request.HttpRequest')
    request.session = None
    request.META = {'HTTP_AUTHORIZATION': token}

    load_backend_mocker = mocker.patch('drf_social_oauth2.authentication.load_backend')
    load_backend_mocker.return_value.do_auth.return_value = None

    authenticated = SocialAuthentication()
    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_header(mocker):
    token = 'Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a'

    request = mocker.patch('django.http.request.HttpRequest')
    request.session = None
    request.META = {'HTTP_AUTHORIZATION': token}

    authenticated = SocialAuthentication()
    text = authenticated.authenticate_header(request)
    assert text == 'Bearer backend realm="api"'
