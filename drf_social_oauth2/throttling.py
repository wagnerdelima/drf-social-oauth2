"""
Throttling for drf-social-oauth2 endpoints.

The token endpoints this package exposes with ``AllowAny`` permissions —
most notably ``/convert-token/``, which performs an outbound HTTP request to
the social provider for every call — are natural brute-force and
amplification targets. This module provides an opt-in scoped throttle for
them.

Throttling is dormant until a rate is configured. To enable it, add rates
for the scopes you care about::

    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_RATES': {
            'drfso2-token': '60/min',
            'drfso2-convert-token': '30/min',
            'drfso2-revoke-token': '30/min',
        },
    }
"""

from rest_framework.throttling import ScopedRateThrottle


class OptInScopedRateThrottle(ScopedRateThrottle):
    """A ScopedRateThrottle that stays inactive until a rate is configured.

    Differences from the stock ``ScopedRateThrottle``:

    - The scope is read from the ``drfso2_throttle_scope`` view attribute
      instead of ``throttle_scope``, so projects that run the stock
      ``ScopedRateThrottle`` globally are unaffected by this package's views.
    - A scope with no configured rate allows the request instead of raising
      ``ImproperlyConfigured``, so shipping scopes on library views does not
      break projects that never configured them.
    """

    scope_attr: str = 'drfso2_throttle_scope'

    def get_rate(self) -> str | None:
        return self.THROTTLE_RATES.get(self.scope)
