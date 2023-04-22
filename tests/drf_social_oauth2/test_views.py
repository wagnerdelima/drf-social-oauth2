import os
from unittest.mock import PropertyMock

from pytest import fixture

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf_social_oauth2.test_settings')

from django.http.request import HttpRequest
from django import setup

setup()

from django.urls import reverse
from rest_framework.test import APIClient
from tests.drf_social_oauth2.drf_fixtures import application, user, save


def create_request(content: str = 'Bearer'):
    request = HttpRequest()
    request.META = {'HTTP_AUTHORIZATION': content}
    request.session = None
    return request


@fixture(scope='module')
def client_api():
    client = APIClient()
    yield client
    del client


def test_convert_token_endpoint_with_no_post_params(client_api):
    response = client_api.post(
        reverse('convert_token'),
        format='json',
    )

    assert response.status_code == 400


def test_convert_token_endpoint_with_missing_params(client_api):
    response = client_api.post(
        reverse('convert_token'),
        data={'grant_type': 'convert_token', 'backend': 'github', 'client_id': ''},
        format='json',
    )

    assert response.status_code == 400


def test_convert_token_endpoint(mocker, client_api, user, application):
    # mocks the validate_token_request. Otherwise, the validator will fail because the request
    # doesn't contain the proper attributes.
    mocker.patch(
        'drf_social_oauth2.oauth2_endpoints.SocialTokenGrant.validate_token_request'
    )

    # mocks the request validator, this way it saved the access token and request token.
    # the validator will use the save() method instead.
    request_validator = mocker.Mock()
    request_validator.save_token = save
    m = mocker.patch(
        'drf_social_oauth2.oauth2_endpoints.SocialTokenGrant.request_validator',
        new_callable=PropertyMock,
    )
    m.return_value = request_validator

    response = client_api.post(
        reverse('convert_token'),
        data={
            'grant_type': 'convert_token',
            'backend': 'facebook',
            'client_id': 'code',
            'client_secret': 'code',
            'token': 'token',
        },
        format='json',
    )
    assert response.status_code == 200
    assert 'access_token' in response.data
    assert 'refresh_token' in response.data
    assert 'expires_in' in response.data
    assert 'token_type' in response.data
    assert 'scope' in response.data


def test_revoke_token_endpoint_with_no_post_params(client_api):
    response = client_api.post(
        reverse('revoke_token'),
        format='json',
    )

    assert response.status_code == 400
