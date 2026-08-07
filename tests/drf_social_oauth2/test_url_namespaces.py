"""
Regression tests for issues #79 and #244 — the social ``complete`` URL must
resolve regardless of how the project wired its URLconf.

Every call site (SocialAuthentication, SocialTokenGrant,
DisconnectBackendView) now goes through
``drf_social_oauth2.utils.reverse_social_complete``, which tries each
plausible namespace spelling instead of assuming one.
"""

from django.http.request import HttpRequest
from django.test import override_settings
from django.urls import NoReverseMatch
from pytest import raises

from drf_social_oauth2.authentication import SocialAuthentication
from drf_social_oauth2.utils import reverse_social_complete


def test_resolves_with_package_urls_as_root():
    """The test settings mount drf_social_oauth2.urls as ROOT_URLCONF, which
    registers social_django's URLs under the plain 'social' namespace."""
    assert reverse_social_complete('google-identity') == (
        '/complete/google-identity/'
    )


def test_resolves_under_documented_namespaced_wiring():
    """Issue #79: with include('drf_social_oauth2.urls', namespace='drf') the
    URL only exists as 'drf:social:complete'. The default-config fallback must
    find it without SOCIAL_AUTH_URL_NAMESPACE being set."""
    with override_settings(ROOT_URLCONF='tests.urls_production'):
        assert reverse_social_complete('google-identity') == (
            '/auth/complete/google-identity/'
        )


def test_resolves_with_social_auth_url_namespace_configured():
    """Issue #244: projects on the documented wiring must set
    SOCIAL_AUTH_URL_NAMESPACE='drf:social' for social_django's own views;
    the old code prepended DRFSO2_URL_NAMESPACE again and produced the
    nonexistent 'drf:drf:social:complete'."""
    with override_settings(
        ROOT_URLCONF='tests.urls_production',
        SOCIAL_AUTH_URL_NAMESPACE='drf:social',
    ):
        assert reverse_social_complete('google-identity') == (
            '/auth/complete/google-identity/'
        )


def test_unresolvable_url_raises_actionable_error():
    with override_settings(ROOT_URLCONF='tests.urls_empty'):
        with raises(NoReverseMatch) as exc_info:
            reverse_social_complete('google-identity')
    # The error must tell the user what to do, not just that reversing failed.
    assert 'SOCIAL_AUTH_URL_NAMESPACE' in str(exc_info.value)


def test_social_authentication_works_under_namespaced_wiring(mocker):
    """Issue #79's user-visible symptom: SocialAuthentication raised
    NoReverseMatch (an HTTP 500) for every request under the documented
    wiring, because it reversed the top-level 'social:complete' name."""
    request = HttpRequest()
    request.META = {
        'HTTP_AUTHORIZATION': 'Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a'
    }
    request.session = None

    mocker.patch('drf_social_oauth2.authentication.load_backend')

    with override_settings(ROOT_URLCONF='tests.urls_production'):
        user, token = SocialAuthentication().authenticate(request)

    assert user
    assert token == '401f7ac837da42b97f613d789819ff93537bee6a'
