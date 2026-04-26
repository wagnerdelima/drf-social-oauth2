"""
End-to-end coverage for issue #253 — token issuance under both Google email
aliases (@gmail.com / @googlemail.com).

Walks the convert-token grant from validate_token_request -> load_backend ->
real GoogleIdentityBackend -> mocked Google HTTP -> social_django pipeline ->
User/UserSocialAuth create-or-reuse -> BearerToken -> save_token ->
real AccessToken/RefreshToken DB rows.

The Google HTTP fetch and the OAuth2 client validator are the only parts
mocked; the deduplication path that #253 fixes (normalization, UID stability,
UserSocialAuth lookup, User reuse) runs for real.
"""

from datetime import datetime, timedelta, timezone
from json import loads

import pytest
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken, Application, RefreshToken
from social_django.models import UserSocialAuth

from drf_social_oauth2 import generate_token
from drf_social_oauth2.oauth2_endpoints import SocialTokenServer

GOOGLE_RESPONSE_BASE = {
    'sub': '12345678901234567890',
    'email_verified': True,
    'name': 'Jane Doe',
    'given_name': 'Jane',
    'family_name': 'Doe',
    'iss': 'https://accounts.google.com',
    'aud': 'test',
}


def _google_response(email: str) -> dict:
    return {**GOOGLE_RESPONSE_BASE, 'email': email}


@pytest.fixture
def google_app(user):
    application, _ = Application.objects.get_or_create(
        user=user,
        client_type='confidential',
        authorization_grant_type='Resource owner password-based',
        name='e2e-google-app',
        client_id='e2e-google-id',
    )
    yield application
    application.delete()


@pytest.fixture(autouse=True)
def isolate_pipeline_state():
    """Tear down anything the pipeline created so tests don't bleed.

    The conftest 'user' fixture deliberately keeps its row across tests, so we
    preserve username='user' and only delete what the pipeline produced.
    Token rows cascade-delete with their owning User.
    """
    yield
    UserSocialAuth.objects.all().delete()
    User.objects.exclude(username='user').delete()


def _build_save_token(application):
    """Closure-bound save_token that persists real OAuth2 token rows.

    Mirrors the conftest `save` helper but uses the per-test application and
    the user attached to the request by validate_token_request.
    """

    def save_token(token_dict: dict, request) -> AccessToken:
        re_token = RefreshToken.objects.create(
            user=request.user,
            token=token_dict['refresh_token'],
            application=application,
        )
        ac_token = AccessToken.objects.create(
            user=request.user,
            token=token_dict['access_token'],
            scope=token_dict['scope'],
            application=application,
            source_refresh_token=re_token,
            expires=datetime.now(tz=timezone.utc)
            + timedelta(seconds=token_dict['expires_in']),
        )
        re_token.access_token = ac_token
        re_token.save()
        return ac_token

    return save_token


def _convert_token(server: SocialTokenServer, application, social_token: str):
    headers, body, status = server.create_token_response(
        uri='/auth/convert-token',
        http_method='POST',
        body={
            'grant_type': 'convert_token',
            'backend': 'google-identity',
            'client_id': application.client_id,
            'token': social_token,
        },
    )
    return status, loads(body) if body else {}


class TestEndToEndGoogleEmailAlias:
    """Issue #253: signing in under @gmail.com and @googlemail.com aliases
    must issue fresh tokens for the same Django user, not duplicate accounts.
    """

    def _server(self, mocker, application: Application) -> SocialTokenServer:
        validator = mocker.Mock()
        validator.save_token = _build_save_token(application)
        return SocialTokenServer(
            request_validator=validator,
            token_generator=generate_token,
        )

    def _patch_google(self, mocker):
        """Mock the redirect_uri reverse() and Google's userinfo HTTP fetch."""
        mocker.patch(
            'drf_social_oauth2.oauth2_grants.reverse',
            return_value='/complete/google-identity/',
        )
        return mocker.patch(
            'drf_social_oauth2.backends.GoogleIdentityBackend.user_data'
        )

    def test_googlemail_then_gmail_issues_tokens_for_one_user(
        self, mocker, google_app
    ):
        user_data = self._patch_google(mocker)
        server = self._server(mocker, google_app)

        # First sign-in: @googlemail.com — pipeline creates the user under
        # the canonical @gmail.com email thanks to normalization.
        user_data.return_value = _google_response('jane.doe@googlemail.com')
        status1, body1 = _convert_token(server, google_app, 'token-googlemail')
        assert status1 == 200, body1
        assert 'access_token' in body1
        assert 'refresh_token' in body1
        assert body1['expires_in'] == 3600
        assert body1['token_type'] == 'Bearer'

        # Second sign-in: @gmail.com — same Google user, must reuse the row.
        user_data.return_value = _google_response('jane.doe@gmail.com')
        status2, body2 = _convert_token(server, google_app, 'token-gmail')
        assert status2 == 200, body2
        assert 'access_token' in body2
        # Each call issues a fresh access and refresh token.
        assert body2['access_token'] != body1['access_token']
        assert body2['refresh_token'] != body1['refresh_token']

        # The deduplication assertions — the heart of issue #253.
        users = User.objects.filter(email='jane.doe@gmail.com')
        assert users.count() == 1
        single = users.first()
        socials = UserSocialAuth.objects.filter(user=single)
        assert socials.count() == 1
        assert socials.first().uid == 'jane.doe@gmail.com'
        assert socials.first().provider == 'google-identity'
        # No @googlemail.com user record leaked through.
        assert not User.objects.filter(email='jane.doe@googlemail.com').exists()
        # Both sign-ins persisted real OAuth2 token rows for the same user.
        assert AccessToken.objects.filter(user=single).count() == 2
        assert RefreshToken.objects.filter(user=single).count() == 2

    def test_gmail_then_googlemail_issues_tokens_for_one_user(
        self, mocker, google_app
    ):
        user_data = self._patch_google(mocker)
        server = self._server(mocker, google_app)

        user_data.return_value = _google_response('jane.doe@gmail.com')
        status1, body1 = _convert_token(server, google_app, 'token-gmail-first')
        assert status1 == 200, body1
        assert 'access_token' in body1

        user_data.return_value = _google_response('jane.doe@googlemail.com')
        status2, body2 = _convert_token(server, google_app, 'token-googlemail')
        assert status2 == 200, body2
        assert body2['access_token'] != body1['access_token']

        single = User.objects.get(email='jane.doe@gmail.com')
        assert UserSocialAuth.objects.filter(user=single).count() == 1
        assert AccessToken.objects.filter(user=single).count() == 2
        assert not User.objects.filter(email='jane.doe@googlemail.com').exists()

    def test_distinct_local_parts_create_distinct_users(
        self, mocker, google_app
    ):
        """Sanity check: normalization only collapses the gmail/googlemail
        domain pair — different local parts must still create different users.
        """
        user_data = self._patch_google(mocker)
        server = self._server(mocker, google_app)

        user_data.return_value = _google_response('alice@googlemail.com')
        status1, _ = _convert_token(server, google_app, 'token-alice')
        assert status1 == 200

        user_data.return_value = _google_response('bob@gmail.com')
        status2, _ = _convert_token(server, google_app, 'token-bob')
        assert status2 == 200

        assert User.objects.filter(email='alice@gmail.com').count() == 1
        assert User.objects.filter(email='bob@gmail.com').count() == 1
        assert UserSocialAuth.objects.count() == 2
        assert {u.uid for u in UserSocialAuth.objects.all()} == {
            'alice@gmail.com',
            'bob@gmail.com',
        }
