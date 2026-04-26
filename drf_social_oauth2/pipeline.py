"""
Custom social_django pipeline steps for drf-social-oauth2.
"""

from typing import Any

from drf_social_oauth2.backends import normalize_google_email_address

# Backend names whose emails should be normalized via the gmail/googlemail
# alias rule. Any backend whose ``name`` starts with ``google`` is covered —
# this captures ``google-oauth2``, ``google-plus``, ``google-identity``, etc.
_GOOGLE_BACKEND_PREFIX: str = 'google'


def normalize_google_email(
    backend: Any, details: dict[str, Any] | None = None, *args: Any, **kwargs: Any
) -> dict[str, Any] | None:
    """Pipeline step that maps @googlemail.com emails to @gmail.com.

    Insert this step **before** ``social_core.pipeline.social_auth.social_uid``
    so the UID computed for Google backends (which defaults to the email) is
    consistent across both domain forms. Without this, the same Google user
    signing in once with @gmail.com and once with @googlemail.com would produce
    two distinct social UIDs and therefore two Django users.

    Example::

        SOCIAL_AUTH_PIPELINE = (
            'social_core.pipeline.social_auth.social_details',
            'drf_social_oauth2.pipeline.normalize_google_email',
            'social_core.pipeline.social_auth.social_uid',
            ...
        )

    Args:
        backend: The active social auth backend instance.
        details: The user details dict produced by ``social_details``.
        *args: Pipeline positional args (unused).
        **kwargs: Pipeline keyword args (unused).

    Returns:
        A dict with the updated ``details`` if normalization changed anything,
        otherwise ``None`` so the pipeline keeps the existing details.
    """
    if not details or not getattr(backend, 'name', '').startswith(_GOOGLE_BACKEND_PREFIX):
        return None

    email = details.get('email')
    normalized = normalize_google_email_address(email)
    if not normalized or normalized == email:
        return None

    new_details = dict(details)
    new_details['email'] = normalized
    if 'username' in new_details and new_details['username'] == email.split('@', 1)[0]:
        new_details['username'] = normalized.split('@', 1)[0]
    return {'details': new_details}
