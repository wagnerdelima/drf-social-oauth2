"""
Settings for drf-social-oauth2.

This module provides configuration settings for the drf-social-oauth2 package.
Settings can be overridden in Django's settings.py.

Available settings:
    DRFSO2_PROPRIETARY_BACKEND_NAME: Name for the proprietary OAuth2 backend.
        Default: "Django"
    DRFSO2_URL_NAMESPACE: URL namespace for drf-social-oauth2 endpoints.
        Default: "drf"
    ACTIVATE_JWT: If True, enables JWT token generation. Activation is wired
        in ``drf_social_oauth2.apps.DRFSocialOauth2Config.ready()``.
        Default: False

Google Identity backend settings:
    SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE: The Google OAuth client ID, or list
        of client IDs, whose ID tokens this application accepts. Required by
        ``GoogleIdentityBackend``; it falls back to
        SOCIAL_AUTH_GOOGLE_IDENTITY_KEY and then
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY, and raises ImproperlyConfigured if none
        is set. Google's tokeninfo endpoint cannot verify that a token was
        issued to this application, so the backend compares the token's 'aud'
        claim against this value. See the "Google OpenID Integration" section
        of the docs.

Refresh token rotation:
    Rotation is implemented and configured entirely by django-oauth-toolkit
    through the ``OAUTH2_PROVIDER`` dict — this package does not alter DOT's
    defaults (``ROTATE_REFRESH_TOKEN`` on, ``REFRESH_TOKEN_REUSE_PROTECTION``
    off, refresh tokens without expiry). Recommended hardening for
    settings.py:

        OAUTH2_PROVIDER = {
            'ROTATE_REFRESH_TOKEN': True,
            'REFRESH_TOKEN_REUSE_PROTECTION': True,
            'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 30,
            'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,  # 14 days
        }
"""

from django.conf import settings

# Name for the proprietary OAuth2 backend
DRFSO2_PROPRIETARY_BACKEND_NAME: str = getattr(
    settings, 'DRFSO2_PROPRIETARY_BACKEND_NAME', "Django"
)

# URL namespace for drf-social-oauth2 endpoints
DRFSO2_URL_NAMESPACE: str = getattr(settings, 'DRFSO2_URL_NAMESPACE', 'drf')
