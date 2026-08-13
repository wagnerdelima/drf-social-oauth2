"""
End-to-end tests for DisconnectBackendView.

The view had no coverage at all, which hid that its redirect-uri reverse()
used the nonexistent 'drf:complete' URL name — every call raised
NoReverseMatch (HTTP 500) under every possible URLconf wiring.
"""

from django.contrib.auth.models import User
from django.urls import reverse
from pytest import fixture
from rest_framework.test import APIClient
from social_django.models import UserSocialAuth


@fixture(scope='function')
def client_api():
    client = APIClient()
    yield client
    del client


@fixture(scope='function')
def association(user):
    """A social login association for the conftest user (who has a usable
    password, so disconnecting the association is allowed)."""
    social = UserSocialAuth.objects.create(
        user=user, provider='google-identity', uid='disconnect-me@gmail.com'
    )
    yield social
    UserSocialAuth.objects.filter(pk=social.pk).delete()


def test_disconnect_backend_removes_association(client_api, user, association):
    client_api.force_authenticate(user=user)

    response = client_api.post(
        reverse('disconnect_backend'),
        data={'backend': 'google-identity', 'association_id': association.id},
        format='json',
    )

    assert response.status_code == 204, getattr(response, 'data', response)
    assert not UserSocialAuth.objects.filter(pk=association.pk).exists()


def test_disconnect_backend_invalid_backend(client_api, user):
    client_api.force_authenticate(user=user)

    response = client_api.post(
        reverse('disconnect_backend'),
        data={'backend': 'not-a-backend', 'association_id': 1},
        format='json',
    )

    assert response.status_code == 400
    assert response.data == {'backend': ['Invalid backend.']}


def test_disconnect_backend_requires_authentication(client_api):
    response = client_api.post(
        reverse('disconnect_backend'),
        data={'backend': 'google-identity', 'association_id': 1},
        format='json',
    )

    assert response.status_code in (401, 403)


def test_disconnect_last_login_method_is_client_error(client_api):
    """A user whose only way in is the association being removed gets a 400
    (NotAllowedToDisconnect), not a 500."""
    lonely = User.objects.create_user(
        username='social-only-user', email='social-only@gmail.com'
    )
    social = UserSocialAuth.objects.create(
        user=lonely, provider='google-identity', uid='social-only@gmail.com'
    )
    client_api.force_authenticate(user=lonely)

    try:
        response = client_api.post(
            reverse('disconnect_backend'),
            data={'backend': 'google-identity', 'association_id': social.id},
            format='json',
        )

        assert response.status_code == 400
        assert UserSocialAuth.objects.filter(pk=social.pk).exists()
    finally:
        UserSocialAuth.objects.filter(pk=social.pk).delete()
        lonely.delete()
