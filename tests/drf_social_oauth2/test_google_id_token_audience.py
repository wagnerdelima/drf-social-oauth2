"""Google ID token audience validation (GHSA-c6x8-38vf-4p8r).

Google's tokeninfo endpoint attests only that an ID token is validly signed and
unexpired; it cannot know which application is asking, so it never checks that
the token was minted for *this* application. Because GoogleIdentityBackend
derives the social UID from the token's email address, a missing audience check
means an ID token obtained through any Google OAuth client — including one the
attacker registered themselves — authenticates its subject here.

These tests pin the audience/issuer/email_verified checks, the settings
resolution order behind them, and the fail-closed behaviour when nothing is
configured.
"""

from json import loads

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from oauth2_provider.models import AccessToken, Application
from social_core.exceptions import AuthTokenError
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from drf_social_oauth2 import generate_token
from drf_social_oauth2.backends import GoogleIdentityBackend, claim_is_true
from drf_social_oauth2.oauth2_endpoints import SocialTokenServer

OWN_CLIENT_ID = 'legit-target-app-456.apps.googleusercontent.com'
ATTACKER_CLIENT_ID = 'attacker-owned-999.apps.googleusercontent.com'
VICTIM_EMAIL = 'victim@example.com'


def _claims(**overrides) -> dict:
    """A tokeninfo response for the victim, minted for our own client."""
    claims = {
        'iss': 'https://accounts.google.com',
        'aud': OWN_CLIENT_ID,
        'sub': '12345678901234567890',
        'email': VICTIM_EMAIL,
        'email_verified': True,
        'name': 'Victim User',
        'given_name': 'Victim',
        'family_name': 'User',
    }
    claims.update(overrides)
    return claims


def _backend() -> GoogleIdentityBackend:
    return GoogleIdentityBackend(
        strategy=load_strategy(request=None),
        redirect_uri='/complete/google-identity/',
    )


class TestAudienceValidation:
    """The core of the advisory: cross-client tokens must be rejected."""

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_token_for_attacker_owned_client_is_rejected(self):
        with pytest.raises(AuthTokenError) as excinfo:
            _backend().validate_id_token_claims(_claims(aud=ATTACKER_CLIENT_ID))

        assert 'different OAuth client' in str(excinfo.value)

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_token_for_own_client_is_accepted(self):
        # No exception means accepted.
        _backend().validate_id_token_claims(_claims())

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_missing_audience_claim_is_rejected(self):
        claims = _claims()
        del claims['aud']

        with pytest.raises(AuthTokenError, match='missing the "aud" claim'):
            _backend().validate_id_token_claims(claims)

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_empty_audience_claim_is_rejected(self):
        with pytest.raises(AuthTokenError, match='missing the "aud" claim'):
            _backend().validate_id_token_claims(_claims(aud=''))

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_substring_audience_does_not_match(self):
        """Matching is exact — a prefix of a real client ID must not pass."""
        with pytest.raises(AuthTokenError):
            _backend().validate_id_token_claims(_claims(aud='legit'))

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=[
            'web-client.apps.googleusercontent.com',
            'ios-client.apps.googleusercontent.com',
        ]
    )
    def test_any_configured_audience_in_a_list_is_accepted(self):
        """Web + iOS + Android client IDs is a normal Google setup."""
        backend = _backend()

        backend.validate_id_token_claims(
            _claims(aud='ios-client.apps.googleusercontent.com')
        )
        backend.validate_id_token_claims(
            _claims(aud='web-client.apps.googleusercontent.com')
        )

        with pytest.raises(AuthTokenError):
            backend.validate_id_token_claims(_claims(aud=ATTACKER_CLIENT_ID))

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_list_valued_aud_claim_is_handled(self):
        """The JWT spec allows a list; tokeninfo returns a string."""
        backend = _backend()

        backend.validate_id_token_claims(
            _claims(aud=[ATTACKER_CLIENT_ID, OWN_CLIENT_ID])
        )

        with pytest.raises(AuthTokenError):
            backend.validate_id_token_claims(_claims(aud=[ATTACKER_CLIENT_ID]))


class TestAudienceSettingResolution:
    """Deployments configured against older docs must keep working."""

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE='from-audience',
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY='from-identity-key',
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY='from-oauth2-key',
    )
    def test_audience_setting_wins(self):
        assert _backend().get_allowed_audiences() == ['from-audience']

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=None,
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY='from-identity-key',
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY='from-oauth2-key',
    )
    def test_falls_back_to_identity_key(self):
        assert _backend().get_allowed_audiences() == ['from-identity-key']

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=None,
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY=None,
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY='from-oauth2-key',
    )
    def test_falls_back_to_google_oauth2_key(self):
        """Releases up to 3.4.1 documented SOCIAL_AUTH_GOOGLE_OAUTH2_KEY here."""
        assert _backend().get_allowed_audiences() == ['from-oauth2-key']

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE='  padded-id  ')
    def test_whitespace_is_stripped(self):
        assert _backend().get_allowed_audiences() == ['padded-id']


class TestFailsClosedWhenUnconfigured:
    """An unconfigured audience must never mean "accept anything".

    Every fallback in the resolution chain is blanked out, so these assert the
    real unconfigured case rather than relying on test_settings' contents.
    """

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=None,
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY=None,
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=None,
    )
    def test_unconfigured_audience_raises(self):
        with pytest.raises(ImproperlyConfigured, match='no Google OAuth client ID'):
            _backend().get_allowed_audiences()

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE='',
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY=None,
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=None,
    )
    def test_empty_audience_raises(self):
        with pytest.raises(ImproperlyConfigured):
            _backend().get_allowed_audiences()

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=['', '   ', None],
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY=None,
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=None,
    )
    def test_list_of_blanks_raises(self):
        with pytest.raises(ImproperlyConfigured):
            _backend().get_allowed_audiences()

    @override_settings(
        SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=None,
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY=None,
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=None,
    )
    def test_validation_does_not_silently_pass_when_unconfigured(self):
        """The failure must happen even for an otherwise well-formed token."""
        with pytest.raises(ImproperlyConfigured):
            _backend().validate_id_token_claims(_claims())


class TestIssuerValidation:
    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    @pytest.mark.parametrize(
        'issuer', ['accounts.google.com', 'https://accounts.google.com']
    )
    def test_google_issuers_are_accepted(self, issuer):
        _backend().validate_id_token_claims(_claims(iss=issuer))

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    @pytest.mark.parametrize(
        'issuer', ['https://accounts.google.com.evil.test', 'evil.test', '', None]
    )
    def test_other_issuers_are_rejected(self, issuer):
        with pytest.raises(AuthTokenError, match='unexpected issuer'):
            _backend().validate_id_token_claims(_claims(iss=issuer))

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_missing_issuer_is_rejected(self):
        claims = _claims()
        del claims['iss']

        with pytest.raises(AuthTokenError, match='unexpected issuer'):
            _backend().validate_id_token_claims(claims)


class TestEmailVerification:
    """The social UID is the email, so an unverified email is a takeover vector."""

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    @pytest.mark.parametrize('verified', [True, 'true', 'True', ' TRUE '])
    def test_verified_email_is_accepted(self, verified):
        _backend().validate_id_token_claims(_claims(email_verified=verified))

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    @pytest.mark.parametrize('verified', [False, 'false', '', None, 0, 'yes'])
    def test_unverified_email_is_rejected(self, verified):
        with pytest.raises(AuthTokenError, match='unverified email'):
            _backend().validate_id_token_claims(_claims(email_verified=verified))

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_missing_email_verified_is_rejected(self):
        claims = _claims()
        del claims['email_verified']

        with pytest.raises(AuthTokenError, match='unverified email'):
            _backend().validate_id_token_claims(claims)


class TestClaimIsTrue:
    @pytest.mark.parametrize('value', [True, 'true', 'TRUE', ' true '])
    def test_truthy(self, value):
        assert claim_is_true(value) is True

    @pytest.mark.parametrize(
        'value', [False, 'false', '', None, 0, 1, 'yes', [], {}, 'truthy']
    )
    def test_falsy(self, value):
        assert claim_is_true(value) is False


class TestUserDataValidatesBeforeReturning:
    """user_data() must not hand unvalidated claims to the social pipeline."""

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_cross_client_token_raises_from_user_data(self, mocker):
        backend = _backend()
        mocker.patch.object(
            backend, 'get_json', return_value=_claims(aud=ATTACKER_CLIENT_ID)
        )

        with pytest.raises(AuthTokenError):
            backend.user_data('any-google-signed-id-token')

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_own_token_is_returned_from_user_data(self, mocker):
        backend = _backend()
        mocker.patch.object(backend, 'get_json', return_value=_claims())

        assert backend.user_data('valid-token')['email'] == VICTIM_EMAIL

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_tokeninfo_is_queried_with_the_id_token(self, mocker):
        backend = _backend()
        get_json = mocker.patch.object(backend, 'get_json', return_value=_claims())

        backend.user_data('the-token')

        get_json.assert_called_once_with(
            GoogleIdentityBackend.TOKENINFO_URL, params={'id_token': 'the-token'}
        )


class TestConvertTokenRejectsCrossClientToken:
    """The advisory's end-to-end scenario, through the real grant.

    Walks POST /convert-token/ -> SocialTokenGrant.validate_token_request ->
    load_backend -> real GoogleIdentityBackend -> mocked Google HTTP, asserting
    that no OAuth2 token is issued and no account is touched.
    """

    @pytest.fixture
    def google_app(self, user):
        application, _ = Application.objects.get_or_create(
            user=user,
            client_type='confidential',
            authorization_grant_type='Resource owner password-based',
            name='audience-test-app',
            client_id='audience-test-id',
        )
        yield application
        application.delete()

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Tear down what the social pipeline created.

        The conftest 'user' fixture deliberately keeps its row across tests, so
        preserve username='user' and drop only pipeline-created records.
        """
        yield
        UserSocialAuth.objects.all().delete()
        User.objects.exclude(username='user').delete()

    def _convert(self, mocker, google_app, claims):
        mocker.patch(
            'drf_social_oauth2.oauth2_grants.reverse',
            return_value='/complete/google-identity/',
        )
        mocker.patch(
            'drf_social_oauth2.backends.GoogleIdentityBackend.get_json',
            return_value=claims,
        )

        validator = mocker.Mock()
        server = SocialTokenServer(
            request_validator=validator, token_generator=generate_token
        )
        headers, body, status = server.create_token_response(
            uri='/auth/convert-token',
            http_method='POST',
            body={
                'grant_type': 'convert_token',
                'backend': 'google-identity',
                'client_id': google_app.client_id,
                'token': 'a-real-google-signed-id-token-for-another-client',
            },
        )
        return status, loads(body) if body else {}

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_no_token_issued_for_attacker_audience(self, mocker, google_app):
        before = AccessToken.objects.count()

        status, body = self._convert(
            mocker, google_app, _claims(aud=ATTACKER_CLIENT_ID)
        )

        assert status != 200, body
        assert 'access_token' not in body
        assert body.get('error') == 'access_denied'
        assert AccessToken.objects.count() == before
        # The victim's account must not have been created or associated.
        assert not UserSocialAuth.objects.filter(uid=VICTIM_EMAIL).exists()

    @override_settings(SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE=OWN_CLIENT_ID)
    def test_token_issued_for_own_audience(self, mocker, google_app):
        """The same flow still works for a token minted for this application."""
        status, body = self._convert(mocker, google_app, _claims())

        assert status == 200, body
        assert 'access_token' in body
        assert UserSocialAuth.objects.filter(uid=VICTIM_EMAIL).exists()
