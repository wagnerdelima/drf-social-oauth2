"""Tests for ACTIVATE_JWT toggle and JWT token generation.

The activation lives in ``drf_social_oauth2.apps.DRFSocialOauth2Config.ready()``.
These tests guard against regressions of the historical bug where users set
``ACTIVATE_JWT = True`` but still received non-JWT access tokens (issue #57).
"""

import jwt
import pytest
from django.conf import settings
from oauth2_provider import settings as oauth2_settings_module

from drf_social_oauth2 import generate_token
from drf_social_oauth2.apps import DRFSocialOauth2Config


@pytest.fixture
def restore_oauth2_defaults():
    """Snapshot and restore the oauth2_provider DEFAULTS keys we mutate."""
    keys = ('ACCESS_TOKEN_GENERATOR', 'REFRESH_TOKEN_GENERATOR')
    saved = {k: oauth2_settings_module.DEFAULTS.get(k) for k in keys}
    yield
    for k, v in saved.items():
        oauth2_settings_module.DEFAULTS[k] = v


def test_generate_token_produces_valid_jwt():
    """generate_token must emit a parseable HS256 JWT signed with SECRET_KEY."""
    token = generate_token(request=None)

    # JWT serializes as three dot-separated base64url segments.
    assert token.count('.') == 2

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    assert isinstance(decoded.get('token'), str)
    assert len(decoded['token']) == 30


def test_ready_activates_jwt_generators_when_flag_enabled(
    monkeypatch, restore_oauth2_defaults
):
    """AppConfig.ready() wires JWT generators only when ACTIVATE_JWT is truthy."""
    oauth2_settings_module.DEFAULTS['ACCESS_TOKEN_GENERATOR'] = None
    oauth2_settings_module.DEFAULTS['REFRESH_TOKEN_GENERATOR'] = None

    monkeypatch.setattr(settings, 'ACTIVATE_JWT', True, raising=False)

    config = DRFSocialOauth2Config.create('drf_social_oauth2')
    config.ready()

    assert (
        oauth2_settings_module.DEFAULTS['ACCESS_TOKEN_GENERATOR']
        == 'drf_social_oauth2.generate_token'
    )
    assert (
        oauth2_settings_module.DEFAULTS['REFRESH_TOKEN_GENERATOR']
        == 'drf_social_oauth2.generate_token'
    )


def test_ready_is_noop_when_flag_disabled(monkeypatch, restore_oauth2_defaults):
    """Without ACTIVATE_JWT, ready() must not touch the token generators."""
    oauth2_settings_module.DEFAULTS['ACCESS_TOKEN_GENERATOR'] = None
    oauth2_settings_module.DEFAULTS['REFRESH_TOKEN_GENERATOR'] = None

    monkeypatch.setattr(settings, 'ACTIVATE_JWT', False, raising=False)

    config = DRFSocialOauth2Config.create('drf_social_oauth2')
    config.ready()

    assert oauth2_settings_module.DEFAULTS['ACCESS_TOKEN_GENERATOR'] is None
    assert oauth2_settings_module.DEFAULTS['REFRESH_TOKEN_GENERATOR'] is None
