"""
Tests for the opt-in throttling on the AllowAny token endpoints.

OptInScopedRateThrottle is dormant until a rate is configured for the scope,
so shipping it on library views changes nothing for existing deployments. It
also reads its scope from ``drfso2_throttle_scope`` rather than
``throttle_scope``, so projects running the stock ScopedRateThrottle globally
are not affected by this package's views.
"""

from django.core.cache import cache
from django.urls import reverse
from pytest import fixture
from rest_framework.test import APIClient

from drf_social_oauth2.throttling import OptInScopedRateThrottle


@fixture(scope='function')
def client_api():
    cache.clear()  # throttle histories live in the default cache
    client = APIClient()
    yield client
    cache.clear()


def test_no_configured_rate_never_throttles(client_api):
    for _ in range(5):
        response = client_api.post(reverse('convert_token'), format='json')
        # 400 = serializer rejected the empty body; the throttle let it in.
        assert response.status_code == 400


def test_configured_rate_throttles(client_api, monkeypatch):
    # THROTTLE_RATES is bound at class definition, so patch the class attr
    # (override_settings on REST_FRAMEWORK would not reach it).
    monkeypatch.setattr(
        OptInScopedRateThrottle,
        'THROTTLE_RATES',
        {'drfso2-convert-token': '1/min'},
    )

    first = client_api.post(reverse('convert_token'), format='json')
    assert first.status_code == 400

    second = client_api.post(reverse('convert_token'), format='json')
    assert second.status_code == 429


def test_scope_isolation_from_stock_scoped_throttle():
    """The views expose drfso2_throttle_scope, not throttle_scope — a global
    stock ScopedRateThrottle must see no scope on them and stay inert."""
    from drf_social_oauth2.views import ConvertTokenView, RevokeTokenView, TokenView

    for view in (TokenView, ConvertTokenView, RevokeTokenView):
        assert not hasattr(view, 'throttle_scope')
        assert hasattr(view, 'drfso2_throttle_scope')
        assert OptInScopedRateThrottle in view.throttle_classes
