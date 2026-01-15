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
