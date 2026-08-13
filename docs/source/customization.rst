Further Customization for Drf-Social-Oauth2
===========================================
This section is meant for further customization of the framework.
Any idea is welcome and will be listed here.

Customize token expiration
^^^^^^^^^^^^^^^^^^^^^^^^^^

To customize the expiration time for tokens, you can easily do so by adjusting the settings in your `settings.py` file.

Simply import the `oauth2_provider` settings and set the `ACCESS_TOKEN_EXPIRE_SECONDS` to your desired value, in seconds.

Here's an example of how to set the expiration time to 6 months:

.. code-block:: python

    # in your settings.py file.
    from oauth2_provider import settings as oauth2_settings

    # expires in 6 months
    oauth2_settings.DEFAULTS['ACCESS_TOKEN_EXPIRE_SECONDS'] = 1.577e7

By customizing the token expiration time, you can fine-tune the security and functionality of your application
to suit your specific needs.

Refresh Token Rotation
^^^^^^^^^^^^^^^^^^^^^^

Refresh token rotation is a security feature that issues a new refresh token each time a refresh token is used
to obtain a new access token. This helps mitigate the risk of refresh token theft.

**How it works:**

1. When a client uses a refresh token to get a new access token, a new refresh token is also issued.
2. The old refresh token is invalidated and cannot be used again.
3. If someone tries to reuse an old refresh token (indicating potential theft), all tokens in that "family" are revoked.

**Configuration:**

These settings belong to django-oauth-toolkit and are read from the
``OAUTH2_PROVIDER`` dict; drf-social-oauth2 does not change their defaults.
Out of the box django-oauth-toolkit rotates refresh tokens but ships with
reuse protection **off** and refresh tokens that **never expire**, so the
recommended hardening is:

.. code-block:: python

    OAUTH2_PROVIDER = {
        # Enable refresh token rotation (django-oauth-toolkit default: True)
        'ROTATE_REFRESH_TOKEN': True,

        # Enable reuse protection - revokes all tokens if a used refresh token
        # is reused (django-oauth-toolkit default: False)
        'REFRESH_TOKEN_REUSE_PROTECTION': True,

        # Grace period in seconds - how long the old refresh token remains
        # valid after rotation to handle concurrent requests
        # (django-oauth-toolkit default: 0)
        'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 30,

        # Refresh token lifetime in seconds - 14 days
        # (django-oauth-toolkit default: None, i.e. refresh tokens never expire)
        'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,

        # Access token lifetime in seconds - 1 hour
        # (django-oauth-toolkit default: 36000, i.e. 10 hours)
        'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    }

**Settings explained:**

- ``ROTATE_REFRESH_TOKEN``: When ``True``, a new refresh token is issued each time a refresh token is used.
- ``REFRESH_TOKEN_REUSE_PROTECTION``: When ``True``, if a refresh token that has already been used is used again,
  all refresh tokens for that user/application are revoked. This protects against token theft.
- ``REFRESH_TOKEN_GRACE_PERIOD_SECONDS``: The number of seconds the old refresh token remains valid after rotation.
  This helps handle race conditions when multiple requests use the same refresh token simultaneously.
- ``REFRESH_TOKEN_EXPIRE_SECONDS``: The absolute lifetime of refresh tokens in seconds.

**Client-side considerations:**

When refresh token rotation is enabled, your client application must:

1. Store the new refresh token returned with each token refresh response.
2. Replace the old refresh token with the new one.
3. Handle the case where a refresh fails due to token reuse (re-authenticate the user).

**Example refresh response:**

.. code-block:: json

    {
        "access_token": "new_access_token_here",
        "refresh_token": "new_refresh_token_here",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "read write"
    }

**Security benefits:**

- **Limits token lifetime**: Even if a refresh token is stolen, it can only be used once.
- **Detects theft**: If an attacker uses a stolen refresh token after the legitimate user has already used it,
  the reuse is detected and all tokens are revoked.
- **Reduces attack window**: The grace period can be set to a small value to minimize the window of vulnerability.

Throttling the token endpoints
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``/token/``, ``/convert-token/`` and ``/revoke-token/`` accept
unauthenticated or lightly-authenticated traffic, and ``/convert-token/``
performs an outbound HTTP request to the social provider on every call —
making them brute-force and amplification targets. The views ship with an
opt-in scoped throttle that stays dormant until you configure a rate:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_RATES': {
            'drfso2-token': '60/min',
            'drfso2-convert-token': '30/min',
            'drfso2-revoke-token': '30/min',
        },
    }

Only the scopes you configure are enforced; the others keep allowing all
traffic. The throttle reads its scope from a package-specific view attribute
(``drfso2_throttle_scope``), so projects that run DRF's stock
``ScopedRateThrottle`` globally are unaffected. Any throttle classes in
``DEFAULT_THROTTLE_CLASSES`` continue to apply to these views as well.

Google Email Alias Normalization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Google treats ``@gmail.com`` and ``@googlemail.com`` as aliases of the same mailbox — the
``@googlemail.com`` form is still used in some regions (e.g. Germany, the UK). However,
``social_core``'s default Google backends derive the social UID from the email address, so
the same Google user signing in once with ``foo@gmail.com`` and once with
``foo@googlemail.com`` would otherwise produce two distinct ``UserSocialAuth`` records and
two Django users.

drf-social-oauth2 normalizes ``@googlemail.com`` to ``@gmail.com`` before the UID is computed,
so both forms map to the same Django user.

**Automatic for GoogleIdentityBackend:**

If you authenticate with ``drf_social_oauth2.backends.GoogleIdentityBackend`` (the OpenID
Connect backend recommended in the :doc:`integration` guide), normalization is applied
automatically — no extra configuration is required.

**Pipeline step for other Google backends:**

If you use a stock ``python-social-auth`` Google backend such as
``social_core.backends.google.GoogleOAuth2``, add the
``drf_social_oauth2.pipeline.normalize_google_email`` step to your ``SOCIAL_AUTH_PIPELINE``,
**before** ``social_core.pipeline.social_auth.social_uid``:

.. code-block:: python

    SOCIAL_AUTH_PIPELINE = (
        'social_core.pipeline.social_auth.social_details',
        # Normalize @googlemail.com -> @gmail.com before the UID is computed.
        'drf_social_oauth2.pipeline.normalize_google_email',
        'social_core.pipeline.social_auth.social_uid',
        'social_core.pipeline.social_auth.auth_allowed',
        'social_core.pipeline.social_auth.social_user',
        'social_core.pipeline.user.get_username',
        'social_core.pipeline.user.create_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details',
    )

The step is a no-op for non-Google backends (matched by a backend name starting with
``google``) and for emails that don't use the ``@googlemail.com`` alias, so it is safe to
leave enabled in mixed-provider deployments.
