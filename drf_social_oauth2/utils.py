"""
Shared helpers for drf-social-oauth2.
"""

from django.conf import settings
from django.urls import NoReverseMatch, reverse


def social_url_namespace() -> str:
    """Return the namespace social_django's URLs are registered under.

    Mirrors ``social_django.views.NAMESPACE`` but reads the setting lazily,
    so it honours ``override_settings`` in tests and projects that configure
    ``SOCIAL_AUTH_URL_NAMESPACE`` late.
    """
    return getattr(settings, 'SOCIAL_AUTH_URL_NAMESPACE', None) or 'social'


def reverse_social_complete(backend_name: str) -> str:
    """Reverse social_django's ``complete`` URL for the given backend.

    The URL name this package must reverse depends on how the project wired
    its URLconf, and historically each call site guessed differently — which
    is the root cause of issues #79 and #244:

    - ``social_django.urls`` included at the top level registers it as
      ``social:complete``.
    - The documented setup — ``include('drf_social_oauth2.urls',
      namespace='drf')`` — nests it as ``drf:social:complete``.
    - Projects that set ``SOCIAL_AUTH_URL_NAMESPACE`` (required for
      social_django's own views under the nested wiring) register it under
      that namespace instead.

    Rather than requiring configuration, try each plausible spelling in order
    of specificity and return the first that resolves.

    Args:
        backend_name: The social backend name (e.g. 'google-oauth2').

    Returns:
        The resolved URL path.

    Raises:
        NoReverseMatch: If no candidate resolves. The message lists every
            name tried and how to fix the URLconf.
    """
    namespace = social_url_namespace()
    drfso2_namespace: str = getattr(settings, 'DRFSO2_URL_NAMESPACE', 'drf')

    candidates = [f'{namespace}:complete']
    if drfso2_namespace and not namespace.startswith(f'{drfso2_namespace}:'):
        candidates.append(f'{drfso2_namespace}:{namespace}:complete')
    if 'social:complete' not in candidates:
        candidates.append('social:complete')

    for name in candidates:
        try:
            return reverse(name, args=(backend_name,))
        except NoReverseMatch:
            continue

    raise NoReverseMatch(
        "Could not resolve social_django's 'complete' URL; tried "
        f"{candidates}. Ensure 'drf_social_oauth2.urls' (or "
        "'social_django.urls') is included in your URLconf. If you include "
        "it under a namespace — e.g. include('drf_social_oauth2.urls', "
        "namespace='drf') — set SOCIAL_AUTH_URL_NAMESPACE accordingly "
        "(e.g. 'drf:social')."
    )
