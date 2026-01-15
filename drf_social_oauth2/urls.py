"""
URL configuration for drf-social-oauth2.

This module defines the URL patterns for OAuth2 endpoints including
token generation, conversion, revocation, and session management.
"""

from django.urls import include, re_path
from oauth2_provider.views import AuthorizationView

from drf_social_oauth2.views import (
    ConvertTokenView,
    DisconnectBackendView,
    InvalidateRefreshTokens,
    InvalidateSessions,
    RevokeTokenView,
    TokenView,
)

app_name = 'drf'

urlpatterns = [
    re_path(r'^authorize/?$', AuthorizationView.as_view(), name='authorize'),
    re_path(r'^token/?$', TokenView.as_view(), name='token'),
    re_path('', include('social_django.urls', namespace='social')),
    re_path(r'^convert-token/?$', ConvertTokenView.as_view(), name='convert_token'),
    re_path(r'^revoke-token/?$', RevokeTokenView.as_view(), name='revoke_token'),
    re_path(
        r'^invalidate-sessions/?$',
        InvalidateSessions.as_view(),
        name='invalidate_sessions',
    ),
    re_path(
        r'^invalidate-refresh-tokens/?$',
        InvalidateRefreshTokens.as_view(),
        name='invalidate_refresh_tokens',
    ),
    re_path(
        r'^disconnect-backend/?$',
        DisconnectBackendView.as_view(),
        name='disconnect_backend',
    ),
]
