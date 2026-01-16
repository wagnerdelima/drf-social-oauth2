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

Add the following to your ``OAUTH2_PROVIDER`` settings in ``settings.py``:

.. code-block:: python

    OAUTH2_PROVIDER = {
        # Enable refresh token rotation (default: True)
        'ROTATE_REFRESH_TOKEN': True,

        # Enable reuse protection - revokes all tokens if a used refresh token
        # is reused (default: True)
        'REFRESH_TOKEN_REUSE_PROTECTION': True,

        # Grace period in seconds - how long the old refresh token remains
        # valid after rotation to handle concurrent requests (default: 0)
        'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 30,

        # Refresh token lifetime in seconds (default: 14 days)
        'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,

        # Access token lifetime in seconds (default: 1 hour)
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
