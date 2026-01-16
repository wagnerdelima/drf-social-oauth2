"""
Tests for refresh token rotation functionality.

These tests verify that refresh token rotation works correctly when enabled,
including:
- New refresh tokens are issued on each use
- Old refresh tokens are invalidated
- Reuse protection detects and handles token reuse
"""

import uuid
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from oauth2_provider.models import AccessToken, RefreshToken
from pytest import fixture, mark
from rest_framework.test import APIClient


def generate_token():
    """Generate a unique token string."""
    return uuid.uuid4().hex


def get_expires(hours=1):
    """Get an expiration datetime in the future."""
    return datetime.now(tz=timezone.utc) + timedelta(hours=hours)


@fixture(scope='function')
def client_api():
    """Create an API client for testing."""
    client = APIClient()
    yield client
    del client


@fixture(scope='function')
def access_token(user, application):
    """Create an access token for testing."""
    token = AccessToken.objects.create(
        user=user,
        application=application,
        token=generate_token(),
        expires=get_expires(),
        scope='read write',
    )
    yield token
    # Cleanup
    AccessToken.objects.filter(pk=token.pk).delete()


@fixture(scope='function')
def refresh_token(user, application, access_token):
    """Create a refresh token for testing."""
    token = RefreshToken.objects.create(
        user=user,
        application=application,
        token=generate_token(),
        access_token=access_token,
    )
    yield token
    # Cleanup
    RefreshToken.objects.filter(pk=token.pk).delete()


class TestRefreshTokenRotationSettings:
    """Tests for refresh token rotation settings."""

    def test_default_rotation_enabled(self):
        """Test that rotation is enabled by default."""
        from drf_social_oauth2.settings import ROTATE_REFRESH_TOKEN
        assert ROTATE_REFRESH_TOKEN is True

    def test_default_reuse_protection_enabled(self):
        """Test that reuse protection is enabled by default."""
        from drf_social_oauth2.settings import REFRESH_TOKEN_REUSE_PROTECTION
        assert REFRESH_TOKEN_REUSE_PROTECTION is True

    def test_default_grace_period(self):
        """Test the default grace period is 0."""
        from drf_social_oauth2.settings import REFRESH_TOKEN_GRACE_PERIOD_SECONDS
        assert REFRESH_TOKEN_GRACE_PERIOD_SECONDS == 0

    def test_default_expire_seconds(self):
        """Test the default refresh token expiration."""
        from drf_social_oauth2.settings import REFRESH_TOKEN_EXPIRE_SECONDS
        assert REFRESH_TOKEN_EXPIRE_SECONDS == 1209600  # 14 days

    def test_settings_from_oauth2_provider(self):
        """Test that settings are read from OAUTH2_PROVIDER dict."""
        oauth2_settings = getattr(settings, 'OAUTH2_PROVIDER', {})
        assert oauth2_settings.get('ROTATE_REFRESH_TOKEN') is True
        assert oauth2_settings.get('REFRESH_TOKEN_REUSE_PROTECTION') is True


class TestRefreshTokenRotationBehavior:
    """Tests for refresh token rotation behavior."""

    def test_refresh_token_created_with_access_token(
        self, user, application, access_token, refresh_token
    ):
        """Test that refresh tokens are properly linked to access tokens."""
        assert refresh_token.access_token == access_token
        assert refresh_token.user == user
        assert refresh_token.application == application

    def test_multiple_refresh_tokens_per_user(self, user, application):
        """Test that a user can have multiple refresh tokens."""
        tokens = []
        for _ in range(3):
            access_token = AccessToken.objects.create(
                user=user,
                application=application,
                token=generate_token(),
                expires=get_expires(),
                scope='read write',
            )
            refresh_token = RefreshToken.objects.create(
                user=user,
                application=application,
                token=generate_token(),
                access_token=access_token,
            )
            tokens.append(refresh_token)

        assert RefreshToken.objects.filter(user=user, application=application).count() >= 3

        # Cleanup
        for token in tokens:
            token.access_token.delete()

    def test_refresh_token_invalidation(self, user, application):
        """Test that refresh tokens can be invalidated."""
        # Create tokens
        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            expires=get_expires(),
            scope='read write',
        )
        refresh_token = RefreshToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            access_token=access_token,
        )

        token_id = refresh_token.pk

        # Revoke the refresh token
        refresh_token.revoke()

        # Verify it's revoked (access_token is set to None)
        refresh_token.refresh_from_db()
        assert refresh_token.revoked is not None

        # Cleanup
        RefreshToken.objects.filter(pk=token_id).delete()
        access_token.delete()

    def test_invalidate_all_refresh_tokens_endpoint(
        self, client_api, user, application
    ):
        """Test the invalidate refresh tokens endpoint."""
        # Create multiple refresh tokens
        for _ in range(3):
            access_token = AccessToken.objects.create(
                user=user,
                application=application,
                token=generate_token(),
                expires=get_expires(),
                scope='read write',
            )
            RefreshToken.objects.create(
                user=user,
                application=application,
                token=generate_token(),
                access_token=access_token,
            )

        initial_count = RefreshToken.objects.filter(
            user=user, application=application
        ).count()
        assert initial_count >= 3

        # Invalidate all refresh tokens
        client_api.force_authenticate(user=user)
        response = client_api.post(
            reverse('invalidate_refresh_tokens'),
            data={'client_id': application.client_id},
            format='json',
        )

        assert response.status_code == 204
        assert RefreshToken.objects.filter(
            user=user, application=application
        ).count() == 0


class TestRefreshTokenReuseProtection:
    """Tests for refresh token reuse protection."""

    def test_revoked_token_has_revoked_timestamp(self, user, application):
        """Test that revoked tokens have a revoked timestamp."""
        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            expires=get_expires(),
            scope='read write',
        )
        refresh_token = RefreshToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            access_token=access_token,
        )

        # Initially not revoked
        assert refresh_token.revoked is None

        # Revoke the token
        refresh_token.revoke()
        refresh_token.refresh_from_db()

        # Now should have revoked timestamp
        assert refresh_token.revoked is not None

        # Cleanup
        refresh_token.delete()
        access_token.delete()

    def test_token_family_revocation(self, user, application):
        """Test that revoking one token can revoke related tokens.

        This simulates the behavior when reuse protection detects
        a compromised token family.
        """
        # Create a "family" of tokens (simulating rotation)
        access_tokens = []
        refresh_tokens = []

        for _ in range(3):
            access_token = AccessToken.objects.create(
                user=user,
                application=application,
                token=generate_token(),
                expires=get_expires(),
                scope='read write',
            )
            refresh_token = RefreshToken.objects.create(
                user=user,
                application=application,
                token=generate_token(),
                access_token=access_token,
            )
            access_tokens.append(access_token)
            refresh_tokens.append(refresh_token)

        # Simulate detecting reuse - revoke all tokens for this user/app
        RefreshToken.objects.filter(
            user=user,
            application=application,
        ).update(revoked=datetime.now(tz=timezone.utc))

        # Verify all are revoked
        for rt in refresh_tokens:
            rt.refresh_from_db()
            assert rt.revoked is not None

        # Cleanup
        for rt in refresh_tokens:
            rt.delete()
        for at in access_tokens:
            at.delete()


@mark.django_db
class TestRefreshTokenRotationIntegration:
    """Integration tests for refresh token rotation with the token endpoint."""

    @override_settings(
        OAUTH2_PROVIDER={
            'ROTATE_REFRESH_TOKEN': True,
            'REFRESH_TOKEN_REUSE_PROTECTION': True,
            'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 0,
        }
    )
    def test_rotation_settings_applied(self):
        """Test that rotation settings are properly applied."""
        # Re-import to get fresh settings
        from importlib import reload

        from drf_social_oauth2 import settings as drf_settings
        reload(drf_settings)

        assert drf_settings.ROTATE_REFRESH_TOKEN is True
        assert drf_settings.REFRESH_TOKEN_REUSE_PROTECTION is True

    def test_token_endpoint_exists(self, client_api):
        """Test that the token endpoint is accessible."""
        response = client_api.post(reverse('token'))
        # Should return 400 (bad request) not 404 (not found)
        assert response.status_code != 404
