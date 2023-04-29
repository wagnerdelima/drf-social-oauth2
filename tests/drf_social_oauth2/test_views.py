import os
from unittest.mock import PropertyMock

from pytest import fixture

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf_social_oauth2.test_settings')

from django import setup

setup()

from django.urls import reverse

from rest_framework.test import APIClient
from oauth2_provider.models import RefreshToken, AccessToken
from model_bakery.recipe import Recipe

from tests.drf_social_oauth2.drf_fixtures import application, user, save


@fixture(scope='function')
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


def test_convert_token_endpoint(mocker, client_api, user):
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


def test_revoke_token_endpoint_with_no_post_params(client_api, user):
    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('revoke_token'),
        format='json',
    )

    assert response.status_code == 400


def test_revoke_token_endpoint_with_missing_params(client_api, user):
    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('revoke_token'),
        data={'client_id': 'id', 'client_secret': 'secret'},
        format='json',
    )

    assert response.status_code == 400


def test_revoke_invalid_token_endpoint(client_api, user, application):
    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('revoke_token'),
        data={'client_id': 'code', 'client_secret': 'code', 'token': 'token'},
        format='json',
    )
    assert response.status_code == 401


def test_revoke_token_endpoint(client_api, user, application):
    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('revoke_token'),
        data={
            'client_id': application.client_id,
            'client_secret': application.client_secret,
            'token': 'token',
        },
        format='json',
    )
    assert response.status_code == 204


def test_invalidate_refresh_tokens_no_authentication(client_api):
    response = client_api.post(
        reverse('invalidate_refresh_tokens'),
        format='json',
    )

    assert response.status_code == 403


def test_invalidate_refresh_tokens_endpoint_with_no_post_params(client_api, user):
    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_refresh_tokens'),
        format='json',
    )

    assert response.status_code == 400


def test_invalidate_refresh_tokens_endpoint(client_api, user, application):
    token_recipe = Recipe(RefreshToken, user=user, application=application)
    token_recipe.make(_quantity=5)

    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_refresh_tokens'),
        data={'client_id': application.client_id},
        format='json',
    )

    assert RefreshToken.objects.filter(user=user, application=application).count() == 0
    assert response.status_code == 204


def test_invalidate_refresh_tokens_endpoint_no_application(
    client_api, user, application
):
    token_recipe = Recipe(AccessToken, user=user, application=application)
    token_recipe.make(_quantity=5)

    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_refresh_tokens'),
        data={'client_id': ''},
        format='json',
    )

    assert response.status_code == 400


def test_invalidate_refresh_tokens_endpoint_invalid_application(
    client_api, user, application
):
    token_recipe = Recipe(AccessToken, user=user, application=application)
    token_recipe.make(_quantity=5)

    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_refresh_tokens'),
        data={'client_id': 'invalid'},
        format='json',
    )

    assert response.status_code == 400


def test_invalidate_sessions_no_authentication(client_api):
    response = client_api.post(
        reverse('invalidate_sessions'),
        format='json',
    )

    assert response.status_code == 403


def test_invalidate_sessions_endpoint_with_no_post_params(client_api, user):
    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_sessions'),
        format='json',
    )

    assert response.status_code == 400


def test_invalidate_sessions_endpoint(client_api, user, application):
    token_recipe = Recipe(AccessToken, user=user, application=application)
    token_recipe.make(_quantity=5)

    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_sessions'),
        data={'client_id': application.client_id},
        format='json',
    )

    assert response.status_code == 204


def test_invalidate_sessions_endpoint_no_application(client_api, user, application):
    token_recipe = Recipe(AccessToken, user=user, application=application)
    token_recipe.make(_quantity=5)

    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_sessions'),
        data={'client_id': ''},
        format='json',
    )

    assert response.status_code == 400


def test_invalidate_sessions_endpoint_invalid_application(
    client_api, user, application
):
    token_recipe = Recipe(AccessToken, user=user, application=application)
    token_recipe.make(_quantity=5)

    client_api.force_authenticate(user=user)
    response = client_api.post(
        reverse('invalidate_sessions'),
        data={'client_id': 'invalid'},
        format='json',
    )

    assert response.status_code == 400
