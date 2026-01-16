"""
Settings for drf-social-oauth2.

This module provides configuration settings for the drf-social-oauth2 package.
Settings can be overridden in Django's settings.py.

Available settings:
    DRFSO2_PROPRIETARY_BACKEND_NAME: Name for the proprietary OAuth2 backend.
        Default: "Django"
    DRFSO2_URL_NAMESPACE: URL namespace for drf-social-oauth2 endpoints.
        Default: "drf"
    ACTIVATE_JWT: If True, enables JWT token generation.
        Default: False

Refresh Token Rotation settings (via OAUTH2_PROVIDER dict):
    ROTATE_REFRESH_TOKEN: If True, a new refresh token is issued each time
        a refresh token is used. Default: True
    REFRESH_TOKEN_REUSE_PROTECTION: If True, detects refresh token reuse
        and revokes all related tokens. Default: True
    REFRESH_TOKEN_GRACE_PERIOD_SECONDS: Number of seconds the old refresh
        token remains valid after rotation (for concurrent requests).
        Default: 0
    REFRESH_TOKEN_EXPIRE_SECONDS: Lifetime of refresh tokens in seconds.
        Default: 1209600 (14 days)

Example configuration in settings.py:
    OAUTH2_PROVIDER = {
        'ROTATE_REFRESH_TOKEN': True,
        'REFRESH_TOKEN_REUSE_PROTECTION': True,
        'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 30,
        'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,  # 14 days
    }
"""

from django.conf import settings
from oauth2_provider import settings as oauth2_settings

# Name for the proprietary OAuth2 backend
DRFSO2_PROPRIETARY_BACKEND_NAME: str = getattr(
    settings, 'DRFSO2_PROPRIETARY_BACKEND_NAME', "Django"
)

# URL namespace for drf-social-oauth2 endpoints
DRFSO2_URL_NAMESPACE: str = getattr(settings, 'DRFSO2_URL_NAMESPACE', 'drf')


# Configure JWT token generation if enabled
if getattr(settings, 'ACTIVATE_JWT', False):
    oauth2_settings.DEFAULTS[
        'ACCESS_TOKEN_GENERATOR'
    ] = 'drf_social_oauth2.generate_token'

    oauth2_settings.DEFAULTS[
        'REFRESH_TOKEN_GENERATOR'
    ] = 'drf_social_oauth2.generate_token'


# Refresh Token Rotation Configuration
# These settings are applied to django-oauth-toolkit's OAUTH2_PROVIDER settings
# Users can override these in their own OAUTH2_PROVIDER dict in settings.py

def get_oauth2_provider_setting(key: str, default: object) -> object:
    """Get a setting from OAUTH2_PROVIDER dict with a fallback default.

    Args:
        key: The setting key to look up.
        default: The default value if not found.

    Returns:
        The setting value or default.
    """
    oauth2_provider_settings = getattr(settings, 'OAUTH2_PROVIDER', {})
    return oauth2_provider_settings.get(key, default)


# Refresh token rotation: issue new refresh token on each use
ROTATE_REFRESH_TOKEN: bool = get_oauth2_provider_setting(
    'ROTATE_REFRESH_TOKEN', True
)

# Reuse protection: revoke all tokens if a used refresh token is reused
REFRESH_TOKEN_REUSE_PROTECTION: bool = get_oauth2_provider_setting(
    'REFRESH_TOKEN_REUSE_PROTECTION', True
)

# Grace period: seconds the old refresh token remains valid after rotation
REFRESH_TOKEN_GRACE_PERIOD_SECONDS: int = get_oauth2_provider_setting(
    'REFRESH_TOKEN_GRACE_PERIOD_SECONDS', 0
)

# Refresh token lifetime in seconds (default: 14 days)
REFRESH_TOKEN_EXPIRE_SECONDS: int = get_oauth2_provider_setting(
    'REFRESH_TOKEN_EXPIRE_SECONDS', 1209600
)
