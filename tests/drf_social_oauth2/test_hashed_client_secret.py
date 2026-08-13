"""
Regression tests for convert-token/revoke-token against applications whose
client secret is hashed (django-oauth-toolkit >= 2.3 hashes on save).

The views inject the Application's *stored* client_secret into the request
body so clients never have to send it. With hashed storage the stock
validator re-hashes the injected value and can never match — every call
failed with invalid_client, and the docs told users to disable the "Hash
client secret" checkbox. ``SocialTokenValidator`` also accepts a presented
secret byte-equal to the stored value, which only the server itself can
inject.

Unlike most view tests in this suite, the convert-token test here runs the
REAL validator chain (client_authentication_required -> authenticate_client
-> _check_secret); only the social provider round-trip is mocked.
"""

from django.urls import reverse
from oauth2_provider.models import AccessToken, Application, RefreshToken
from oauth2_provider.oauth2_validators import OAuth2Validator
from pytest import fixture
from rest_framework.test import APIClient

from drf_social_oauth2.oauth2_validators import SocialTokenValidator


@fixture(scope='function')
def client_api():
    client = APIClient()
    yield client
    del client


@fixture(scope='function')
def hashed_secret_application(user):
    """An Application saved the DOT >= 2.3 way: generated secret, hashed at
    rest. authorization_grant_type must be a real choice value ('password',
    not the human-readable label) or the real validator rejects the grant."""
    application = Application.objects.create(
        user=user,
        client_type='confidential',
        authorization_grant_type='password',
        name='hashed-secret-app',
        client_id='hashed-secret-id',
    )
    yield application
    application.delete()


class TestSocialTokenValidatorCheckSecret:
    def test_stock_validator_rejects_injected_hash(self):
        """Documents the bug: what the view injects is the stored hash, and
        check_password(hash, hash) can never succeed."""
        from django.contrib.auth.hashers import make_password

        stored_hash = make_password('s3cret')
        assert OAuth2Validator()._check_secret(stored_hash, stored_hash) is False

    def test_accepts_injected_stored_hash(self):
        from django.contrib.auth.hashers import make_password

        stored_hash = make_password('s3cret')
        assert SocialTokenValidator()._check_secret(stored_hash, stored_hash) is True

    def test_still_accepts_real_cleartext_secret(self):
        from django.contrib.auth.hashers import make_password

        stored_hash = make_password('s3cret')
        assert SocialTokenValidator()._check_secret('s3cret', stored_hash) is True

    def test_still_rejects_wrong_secret(self):
        from django.contrib.auth.hashers import make_password

        stored_hash = make_password('s3cret')
        assert SocialTokenValidator()._check_secret('wrong', stored_hash) is False
        assert SocialTokenValidator()._check_secret('', stored_hash) is False


class TestConvertTokenWithHashedSecret:
    def test_convert_token_succeeds_with_hashed_client_secret(
        self, mocker, client_api, user, hashed_secret_application
    ):
        backend = mocker.patch('drf_social_oauth2.oauth2_grants.load_backend')
        backend.return_value.do_auth.return_value = user

        response = client_api.post(
            reverse('convert_token'),
            data={
                'grant_type': 'convert_token',
                'backend': 'facebook',
                'client_id': hashed_secret_application.client_id,
                'token': 'social-provider-token',
            },
            format='json',
        )

        assert response.status_code == 200, response.data
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data

        # Real DB rows were written through the real validator.
        token = AccessToken.objects.get(token=response.data['access_token'])
        assert token.user == user
        assert token.application == hashed_secret_application

        AccessToken.objects.filter(application=hashed_secret_application).delete()
        RefreshToken.objects.filter(application=hashed_secret_application).delete()

    def test_revoke_token_succeeds_with_hashed_client_secret(
        self, client_api, user, hashed_secret_application
    ):
        client_api.credentials(HTTP_AUTHORIZATION='Bearer some-token')
        client_api.force_authenticate(user=user)

        response = client_api.post(
            reverse('revoke_token'),
            data={'client_id': hashed_secret_application.client_id},
            format='json',
        )

        # RFC 7009: revocation of an unknown token is still a success — but
        # only after client authentication passed. With the stock validator
        # this returned 401 invalid_client.
        assert response.status_code == 204, response.data
