import os
from json import loads
from datetime import datetime, timedelta, timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf_social_oauth2.test_settings')

from django import setup

setup()

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone

from oauth2_provider.models import Application, AccessToken, RefreshToken
from pytest import fixture

from drf_social_oauth2.oauth2_endpoints import SocialTokenServer
from drf_social_oauth2 import generate_token


@fixture(scope='function')
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
    del user


@fixture(scope='function')
def application(user):
    app, _ = Application.objects.get_or_create(
        user=user,
        client_type='confidential',
        authorization_grant_type='Resource owner password-based',
        name='app',
    )

    yield app
    del app


def save(token, request):
    u = User.objects.get(email='test@email.com')
    app = Application.objects.get(user=u.id)
    re_token = RefreshToken.objects.create(
        user=u, token=token['refresh_token'], application=app,
    )
    ac_token = AccessToken.objects.create(
        user=u,
        token=token['access_token'],
        scope=token['scope'],
        application=app,
        source_refresh_token=re_token,
        expires=datetime.now(tz=timezone.utc) + timedelta(seconds=token['expires_in']),
    )
    re_token.access_token = ac_token
    re_token.save()

    return ac_token


def assign_request_application(request):
    u = User.objects.get(email='test@email.com')
    app = Application.objects.get(user=u.id)
    request.client = app


def test_create_social_token(mocker, user, application):
    """
    Creates a social token.
    """
    request_validator = mocker.Mock()
    request_validator.save_token = save

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


def test_reuse_social_token(mocker, user, application):
    request_validator = mocker.Mock()
    request_validator.save_token = save
    request_validator.client_authentication_required = assign_request_application

    mocker.patch('drf_social_oauth2.oauth2_grants.reverse')
    backend = mocker.patch('drf_social_oauth2.oauth2_grants.load_backend')
    backend.return_value.do_auth.return_value = user

    social = SocialTokenServer(
        request_validator=request_validator, token_generator=generate_token,
    )

    uri = (
        f'/auth/convert-token/?grant_type=convert_token&'
        f'backend=facebook&client_id={application.client_id}&client_secret={application.client_secret}&token=token'
    )
    # create the first token.
    _, data, status = social.create_token_response(uri=uri, http_method='POST', body='')

    # if an access token already exists, then the token is returned and no new token is created.
    _, data, status = social.create_token_response(uri=uri, http_method='POST', body='')
    data = loads(data)

    assert status == 200
    assert 'access_token' in data
    # if there is a valid token, the expiry date will be smaller than the number when the token was created.
    assert data['expires_in'] < 3600


def test_social_token_expired(mocker, user, application):
    request_validator = mocker.Mock()
    request_validator.save_token = save
    request_validator.client_authentication_required = assign_request_application

    mocker.patch('drf_social_oauth2.oauth2_grants.reverse')
    backend = mocker.patch('drf_social_oauth2.oauth2_grants.load_backend')
    backend.return_value.do_auth.return_value = user

    social = SocialTokenServer(
        request_validator=request_validator, token_generator=generate_token,
    )

    uri = (
        f'/auth/convert-token/?grant_type=convert_token&'
        f'backend=facebook&client_id={application.client_id}&client_secret={application.client_secret}&token=token'
    )
    # create the first token.
    _, data, status = social.create_token_response(uri=uri, http_method='POST', body='')
    data = loads(data)

    # if the access token is expired, a nw access token is generated.
    access_token = AccessToken.objects.get(token=data['access_token'])
    access_token.expires = datetime.now(tz=timezone.utc)
    access_token.save()

    # if an access token already exists, then the token is returned and no new token is created.
    _, data, status = social.create_token_response(uri=uri, http_method='POST', body='')
    data = loads(data)

    assert status == 200
    assert 'access_token' in data
    # if there is a valid token, the expiry date will be smaller than the number when the token was created.
    assert data['expires_in'] == 3600
