"""Django AppConfig for drf-social-oauth2."""

from django.apps import AppConfig


class DRFSocialOauth2Config(AppConfig):
    """AppConfig for drf-social-oauth2.

    The ``ready()`` hook wires JWT token generation into django-oauth-toolkit
    when the user opts in via ``ACTIVATE_JWT = True``. Doing this in
    ``ready()`` (instead of as an import side effect of ``settings.py``)
    guarantees the activation runs once, after Django is fully initialized,
    and before any request can reach the token endpoint.
    """

    name = 'drf_social_oauth2'

    def ready(self) -> None:
        from django.conf import settings

        if not getattr(settings, 'ACTIVATE_JWT', False):
            return

        from oauth2_provider import settings as oauth2_settings

        oauth2_settings.DEFAULTS[
            'ACCESS_TOKEN_GENERATOR'
        ] = 'drf_social_oauth2.generate_token'
        oauth2_settings.DEFAULTS[
            'REFRESH_TOKEN_GENERATOR'
        ] = 'drf_social_oauth2.generate_token'
