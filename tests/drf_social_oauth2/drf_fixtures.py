from datetime import datetime, timedelta, timezone

from pytest import fixture

from django.contrib.auth.models import User
from django.db import IntegrityError

from oauth2_provider.models import Application, AccessToken, RefreshToken


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
        user = User.objects.get(
            username='user',
            email='test@email.com',
        )

    yield user
    del user


def save(token, request):
    u = User.objects.get(email='test@email.com')
    app = Application.objects.get(user=u.id)
    re_token = RefreshToken.objects.create(
        user=u,
        token=token['refresh_token'],
        application=app,
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
