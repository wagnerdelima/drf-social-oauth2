import os
from json import loads

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf_social_oauth2.test_settings')

from django import setup

setup()

from django.contrib.auth.models import User
from django.db import IntegrityError

from pytest import fixture

from drf_social_oauth2.oauth2_endpoints import SocialTokenServer
from drf_social_oauth2 import generate_token


@fixture(scope='module')
def user():
    """
    Creates a user in database. this is a mock user, it's deletes after test runs.
    """
    try:
        user = User.objects.create_user(
            username='user', email='test@email.com', password='password'
        )
    except IntegrityError:
        user = User.objects.get(username='user', email='test@email.com',)

    yield user
    user.delete()
    del user


def test_create_social_token(mocker, user):
    """
    Creates a social token.
    """
    request_validator = mocker.Mock()
    mocker.patch('drf_social_oauth2.oauth2_grants.reverse')
    backend = mocker.patch('drf_social_oauth2.oauth2_grants.load_backend')
    backend.return_value.do_auth.return_value = user

    social = SocialTokenServer(
        request_validator=request_validator, token_generator=generate_token,
    )

    uri = '/auth/convert-token/?grant_type=convert_token&backend=facebook&client_id=code&client_secret=code&token=token'
    _, data, status = social.create_token_response(uri=uri, http_method='POST', body='')
    data = loads(data)

    assert status == 200
    assert 'access_token' in data
    assert data['expires_in'] == 3600
