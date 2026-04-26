"""
Tests for gmail/googlemail email-alias normalization (issue #253).

Google treats @gmail.com and @googlemail.com as aliases for the same mailbox.
Without normalization, the social-auth pipeline derives a different social UID
for each form (since Google's default UID is the email), so the same user
signing in under both forms would create two Django users.
"""

from unittest.mock import Mock

import pytest

from drf_social_oauth2.backends import (
    GoogleIdentityBackend,
    normalize_google_email_address,
)
from drf_social_oauth2.pipeline import normalize_google_email


class TestNormalizeGoogleEmailAddress:
    @pytest.mark.parametrize(
        'value,expected',
        [
            ('foo@googlemail.com', 'foo@gmail.com'),
            ('Foo.Bar@googlemail.com', 'Foo.Bar@gmail.com'),
            ('foo@GOOGLEMAIL.COM', 'foo@gmail.com'),
            ('foo@gmail.com', 'foo@gmail.com'),
            ('foo@example.com', 'foo@example.com'),
            ('', ''),
            (None, None),
            ('not-an-email', 'not-an-email'),
        ],
    )
    def test_normalizes_googlemail_to_gmail(self, value, expected):
        assert normalize_google_email_address(value) == expected

    def test_preserves_local_part(self):
        assert (
            normalize_google_email_address('first.last+tag@googlemail.com')
            == 'first.last+tag@gmail.com'
        )


class TestGoogleIdentityBackendDetails:
    def _build_backend(self) -> GoogleIdentityBackend:
        backend = GoogleIdentityBackend.__new__(GoogleIdentityBackend)
        backend.strategy = Mock()
        backend.strategy.setting.return_value = None
        return backend

    def test_get_user_details_normalizes_googlemail_email(self):
        backend = self._build_backend()
        response = {
            'email': 'jane.doe@googlemail.com',
            'name': 'Jane Doe',
            'given_name': 'Jane',
            'family_name': 'Doe',
        }

        details = backend.get_user_details(response)

        assert details['email'] == 'jane.doe@gmail.com'
        assert details['username'] == 'jane.doe'

    def test_get_user_details_leaves_gmail_unchanged(self):
        backend = self._build_backend()
        response = {
            'email': 'jane.doe@gmail.com',
            'name': 'Jane Doe',
            'given_name': 'Jane',
            'family_name': 'Doe',
        }

        details = backend.get_user_details(response)

        assert details['email'] == 'jane.doe@gmail.com'
        assert details['username'] == 'jane.doe'

    def test_get_user_id_matches_for_googlemail_and_gmail(self):
        """
        Both forms must produce the same UID, which is the bug's root cause:
        BaseGoogleAuth.get_user_id returns details['email'] by default.
        """
        backend = self._build_backend()
        gmail = backend.get_user_details(
            {'email': 'jane.doe@gmail.com', 'name': '', 'given_name': '', 'family_name': ''}
        )
        googlemail = backend.get_user_details(
            {'email': 'jane.doe@googlemail.com', 'name': '', 'given_name': '', 'family_name': ''}
        )

        gmail_uid = backend.get_user_id(gmail, {})
        googlemail_uid = backend.get_user_id(googlemail, {})

        assert gmail_uid == googlemail_uid == 'jane.doe@gmail.com'


class TestNormalizeGoogleEmailPipeline:
    def test_normalizes_for_google_backend(self):
        backend = Mock()
        backend.name = 'google-oauth2'
        details = {'email': 'jane@googlemail.com', 'username': 'jane'}

        result = normalize_google_email(backend, details)

        assert result == {'details': {'email': 'jane@gmail.com', 'username': 'jane'}}

    def test_updates_username_when_derived_from_email_local_part(self):
        backend = Mock()
        backend.name = 'google-identity'
        details = {'email': 'a.b@googlemail.com', 'username': 'a.b'}

        result = normalize_google_email(backend, details)

        assert result['details']['username'] == 'a.b'
        assert result['details']['email'] == 'a.b@gmail.com'

    def test_preserves_custom_username(self):
        backend = Mock()
        backend.name = 'google-oauth2'
        details = {'email': 'jane@googlemail.com', 'username': 'jane_custom'}

        result = normalize_google_email(backend, details)

        assert result['details']['username'] == 'jane_custom'
        assert result['details']['email'] == 'jane@gmail.com'

    def test_no_op_for_gmail(self):
        backend = Mock()
        backend.name = 'google-oauth2'
        details = {'email': 'jane@gmail.com', 'username': 'jane'}

        assert normalize_google_email(backend, details) is None

    def test_no_op_for_non_google_backend(self):
        backend = Mock()
        backend.name = 'facebook'
        details = {'email': 'jane@googlemail.com', 'username': 'jane'}

        assert normalize_google_email(backend, details) is None

    def test_no_op_when_details_missing(self):
        backend = Mock()
        backend.name = 'google-oauth2'

        assert normalize_google_email(backend, None) is None
        assert normalize_google_email(backend, {}) is None
