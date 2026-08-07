Change log
==========

3.5.0 - 2026-08-07
------------------

## Security

* ``SocialAuthentication`` now rejects inactive users. The ``/convert-token`` grant already refused to issue tokens to ``is_active=False`` users, but the per-request ``Authorization: Bearer <backend> <token>`` path authenticated them anyway, so deactivating an account did not lock it out of the API.
* Fix a cross-request race in ``SocialTokenServer``. django-oauth-toolkit caches its oauthlib core — and with it the server instance — per view class, so the Django request stored on the instance was shared by every in-flight request. Under threaded servers two concurrent ``/convert-token`` calls could swap request objects, running one user's social login with another user's session/META. The request now lives in a ``ContextVar``, isolated per thread/async context.
* Social provider error bodies are no longer echoed to API clients by ``SocialAuthentication`` and the convert-token grant. The upstream response is logged for operators; clients receive only the provider's HTTP status code.
* New opt-in throttling for the ``/token/``, ``/convert-token/`` and ``/revoke-token/`` endpoints (``drfso2-token``, ``drfso2-convert-token``, ``drfso2-revoke-token`` scopes). Dormant until you configure ``DEFAULT_THROTTLE_RATES``; uses a package-specific view attribute so projects running DRF's stock ``ScopedRateThrottle`` globally are unaffected. See the customization docs.

## What's Changed

* **Applications with hashed client secrets now work** (django-oauth-toolkit >= 2.3 hashes ``client_secret`` on save). ``ConvertTokenView`` and ``RevokeTokenView`` inject the stored secret server-side so clients never send it, but the stock validator re-hashes the presented value and could never match a hashed one — every call failed with ``invalid_client``, and the docs told users to disable the "Hash client secret" checkbox. The new ``drf_social_oauth2.oauth2_validators.SocialTokenValidator`` (used only by those two views) additionally accepts a presented secret byte-equal to the stored value. Real cleartext secrets still validate; ``TokenView``'s password grant keeps the stock validator. You can re-enable the hash checkbox on existing applications. django-oauth-toolkit >= 2.3.0 is now required.
* **Fix URL namespace resolution for the social ``complete`` URL** (`#79 <https://github.com/wagnerdelima/drf-social-oauth2/issues/79>`_, `#244 <https://github.com/wagnerdelima/drf-social-oauth2/issues/244>`_). ``SocialAuthentication`` reversed ``social:complete`` (a 500 under the documented ``include(..., namespace='drf')`` wiring), the convert-token grant produced ``drf:drf:social:complete`` when ``SOCIAL_AUTH_URL_NAMESPACE='drf:social'`` was set, and ``DisconnectBackendView`` reversed the nonexistent ``drf:complete`` — making the disconnect endpoint a guaranteed 500 under every wiring. All three now use ``drf_social_oauth2.utils.reverse_social_complete``, which tries each plausible namespace spelling and raises an actionable error naming ``SOCIAL_AUTH_URL_NAMESPACE`` if none resolves. No configuration change is required for existing deployments.
* ``DisconnectBackendView`` returns ``HTTP 400`` instead of crashing when the association is the user's only login method (``NotAllowedToDisconnect``).
* Converted tokens honour the project's configured default scopes (``OAUTH2_PROVIDER['SCOPES']``/``DEFAULT_SCOPES``) instead of a hardcoded ``read write``.
* ``ConvertTokenView`` no longer 500s after a successful conversion when the custom ``AUTH_USER_MODEL`` lacks ``email``, ``first_name`` or ``last_name`` attributes.
* The ``createapp`` management command prints the generated ``client_id`` and ``client_secret`` (the secret is hashed at rest, so this is the only chance to capture it) and exits with a clear error instead of an ``IndexError`` when no superuser exists.
* Removed the dead ``ROTATE_REFRESH_TOKEN``, ``REFRESH_TOKEN_REUSE_PROTECTION``, ``REFRESH_TOKEN_GRACE_PERIOD_SECONDS`` and ``REFRESH_TOKEN_EXPIRE_SECONDS`` constants from ``drf_social_oauth2.settings``. They were never consumed by any code and implied defaults that django-oauth-toolkit does not actually apply (its real defaults: rotation on, reuse protection **off**, refresh tokens never expire). Configure these in ``OAUTH2_PROVIDER``; the customization docs show the recommended hardening.
* The test suite runs without Docker: ``DRFSO2_TEST_DB=sqlite`` switches the test settings to SQLite.
* Documentation: modernized the URLconf examples (the old ones used ``patterns()``, removed in Django 1.10), documented ``SOCIAL_AUTH_URL_NAMESPACE = 'drf:social'``, corrected the refresh-token-rotation defaults, and added the throttling guide.

3.4.2 - 2026-07-30
------------------

## Security

* **Fix an authentication bypass in ``GoogleIdentityBackend`` that allowed account takeover** (`GHSA-c6x8-38vf-4p8r <https://github.com/wagnerdelima/drf-social-oauth2/security/advisories/GHSA-c6x8-38vf-4p8r>`_, CWE-287, CVSS 3.1 8.1 High). Affects every release up to and including 3.4.1 that enables the ``google-identity`` backend.

  ``GoogleIdentityBackend.user_data`` forwarded the caller-supplied ``id_token`` to Google's tokeninfo endpoint and trusted the returned claims without checking the token's ``aud`` (audience) claim against the application's own Google OAuth client ID. python-social-auth performs no such check either, so *any* validly-signed Google ID token was accepted — including one minted for an OAuth client the attacker registered. Because the social UID is derived from the token's email address, an attacker who got a victim to sign in once through their own "Sign in with Google" page could replay the resulting token against the unauthenticated ``/convert-token/`` endpoint and receive a real access token for the victim's account, with no knowledge of the victim's credentials.

  * ``GoogleIdentityBackend.validate_id_token_claims`` now rejects tokens whose ``aud`` does not name a configured client ID, whose ``iss`` is not Google, or whose ``email_verified`` claim is not true.
  * New ``SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE`` setting accepts a client ID or a list of them, for deployments with separate web/iOS/Android clients. It falls back to ``SOCIAL_AUTH_GOOGLE_IDENTITY_KEY`` and then ``SOCIAL_AUTH_GOOGLE_OAUTH2_KEY``, which is what releases up to 3.4.1 documented for this backend — so most existing deployments need no configuration change.
  * New ``drf_social_oauth2.backends.claim_is_true`` helper, since tokeninfo has returned boolean claims both as JSON booleans and as ``"true"``/``"false"`` strings.

  **Action required.** If you enable the ``google-identity`` backend and set *none* of the three settings above, the backend now raises ``ImproperlyConfigured`` instead of accepting unvalidated tokens. This is deliberate: with no configured client ID there is nothing to validate ``aud`` against. Set ``SOCIAL_AUTH_GOOGLE_IDENTITY_AUDIENCE`` to your application's Google OAuth client ID.

  Also note that ID tokens from Google's OAuth 2.0 Playground are now rejected unless you configure the Playground with your own OAuth credentials, because they are minted under Google's Playground client ID. See :doc:`integration`.

## What's Changed

* Fix ``ImportError`` on install with current dependencies. ``setup.py`` requires ``social-auth-app-django>=5.0.0`` with no upper bound, which now resolves to a release depending on ``social-auth-core>=5.0.0`` — where ``GooglePlusAuth`` (named after a product retired in 2019) no longer exists, so ``drf_social_oauth2.backends`` failed at import time. ``GoogleIdentityBackend`` now extends ``GoogleOAuth2``, which is present across ``social-auth-core`` 4.x and 5.x. Both classes derive from the same ``BaseGoogleOAuth2API``/``BaseOAuth2`` bases and use the same Google endpoints; the ``/convert-token`` flow is unchanged. The differences are ``DEFAULT_SCOPE`` (the retired ``plus.login``/``plus.me`` scopes become ``openid``/``email``/``profile``) and ``EXTRA_DATA``, neither of which the ID token flow consumes.

3.4.1 - 2026-04-26
------------------

## What's Changed
* Return ``HTTP 409 Conflict`` instead of ``HTTP 500`` when ``/convert-token`` collides with an existing local user that shares the same email as the social account (`#57 <https://github.com/wagnerdelima/drf-social-oauth2/issues/57>`_).

  * New ``drf_social_oauth2.views._is_email_already_exists`` helper detects unique-email-constraint violations across PostgreSQL, MySQL, and SQLite, and walks the exception chain so it still matches when an ``IntegrityError`` is wrapped in a ``TransactionManagementError`` by a surrounding atomic block.
  * ``ConvertTokenView`` now catches both ``IntegrityError`` and ``TransactionManagementError`` and returns a structured body the frontend can dispatch on:

    .. code-block:: json

        {
          "code": "email_already_exists",
          "detail": "A user with this email already exists for a different authentication method.",
          "backend": "google-oauth2"
        }

  * Recommended companion config: add ``social_core.pipeline.social_auth.associate_by_email`` to ``SOCIAL_AUTH_PIPELINE`` (before ``create_user``) so the duplicate-email path *associates* the social identity with the existing local user rather than throwing. Only enable this for backends that verify email ownership (e.g. Google, Facebook).
* Move JWT activation logic out of ``settings.py`` and into a new ``DRFSocialOauth2Config.ready()`` AppConfig hook, so the activation runs once after Django is fully initialized. Opt in by setting ``ACTIVATE_JWT = True`` in your project settings; see the installation docs for the response shape and caveats.
* ``InvalidateSessions`` and ``InvalidateRefreshTokens`` no longer emit a ``Content-Type`` header on their ``HTTP 204 No Content`` responses (empty dict removed from the ``Response`` call).

3.3.0 - 2026-04-26
------------------

## What's Changed
* Fix duplicate Django users created when the same Google account signs in under both ``@gmail.com`` and ``@googlemail.com`` aliases (`#253 <https://github.com/wagnerdelima/drf-social-oauth2/issues/253>`_).

  * ``drf_social_oauth2.backends.GoogleIdentityBackend`` now normalizes ``@googlemail.com`` to ``@gmail.com`` automatically in ``get_user_details``.
  * New ``drf_social_oauth2.pipeline.normalize_google_email`` pipeline step for users on stock python-social-auth Google backends (e.g. ``social_core.backends.google.GoogleOAuth2``). Insert it before ``social_core.pipeline.social_auth.social_uid`` in ``SOCIAL_AUTH_PIPELINE``.
  * New ``drf_social_oauth2.backends.normalize_google_email_address`` helper.

See the :doc:`customization` guide for configuration details.

2.1.1 - 2023-04-26
------------------

## What's Changed
* 175 create readthedocs documentation by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/176
* Running convert-token for the second time returns html headers with user environment variables by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/177

**Full Changelog**: https://github.com/wagnerdelima/drf-social-oauth2/compare/2.1.0...2.1.1

2.1.0 - 2023-04-24
------------------

## What's Changed
* chore: 👷 fix codecov.yml by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/165
* doc: 📝 add CONTRIBUTING.md file. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/166
* Create SECURITY.md by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/167
* 104 use serializers for views by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/170
* docs: 📝 add missing documentation about invalidate refresh tokens. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/173
* Update CHANGELOG.rst by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/174

**Full Changelog**: https://github.com/wagnerdelima/drf-social-oauth2/compare/2.0.0...2.1.0


2.0.0 - 2023-04-16
------------------

## What's Changed
* Google id token setup by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/163
* Create codecov.yml by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/164

**Full Changelog**: https://github.com/wagnerdelima/drf-social-oauth2/compare/1.3.0...2.0.0


1.3.0 - 2023-04-02
------------------

## What's Changed
* GitHub Sign In by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/157
* bug: 🐛 improve imports, typing and fix a revoke token bug. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/158
* Add Invalidate all Refresh Tokens by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/160
* Exception Handling for Missing Cliend id and Client Token by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/161
* Handling exceptions by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/162

**Full Changelog**: https://github.com/wagnerdelima/drf-social-oauth2/compare/1.2.2...1.3.0


1.2.2 - 2023-03-26
------------------

## What's Changed
* Update issue templates by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/113
* [Snyk] Security upgrade python from 3.9.4-slim-buster to slim-buster by @snyk-bot in https://github.com/wagnerdelima/drf-social-oauth2/pull/121
* Update __init__.py by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/128
* Create CODE_OF_CONDUCT.md by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/145
* Add refresh token generator by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/153
* chore: 🔧 remove 'working next tasks'. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/155
* chore: 🔧 add new version. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/156

## New Contributors
* @snyk-bot made their first contribution in https://github.com/wagnerdelima/drf-social-oauth2/pull/121

**Full Changelog**: https://github.com/wagnerdelima/drf-social-oauth2/compare/1.2.1...1.2.2


1.2.1 - 2022-06-02
------------------

## What's Changed
* Use django timezone.now() in existing token expires_in calculation by @smithumble in https://github.com/wagnerdelima/drf-social-oauth2/pull/109
* release: add version and update changelog. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/112

## New Contributors
* @smithumble made their first contribution in https://github.com/wagnerdelima/drf-social-oauth2/pull/109

**Full Changelog**: https://github.com/wagnerdelima/drf-social-oauth2/compare/1.2.0...1.2.1


1.2.0 - 2022-01-14
------------------

## What's Changed
* Add missing python-jose dependency by @denizdogan in https://github.com/wagnerdelima/drf-social-oauth2/pull/100
* Create FUNDING.yml by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/102
* feat: prevent access tokens from being recreated by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/103

## New Contributors
* @denizdogan made their first contribution in https://github.com/wagnerdelima/drf-social-oauth2/pull/100

1.1.4 - 2021-12-29
------------------

## What's Changed
* Add buy me a coffee button by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/94
* docs: add facebook sample repo. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/95
* Add CI/CD for running tests by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/97
* docs: open api specification. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/96
* chore: new release and CHANGELOGS updated. . 🚀 by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/98


1.1.3 - 2021-12-24
------------------

## What's Changed
* docs: add expiry info for access tokens. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/86
* Feat/disconnect backend by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/87


1.1.2 - 2021-12-19
------------------

## What's Changed
*Increase test coverage by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/84


1.1.1 - 2021-12-17
------------------

## What's Changed
- chore: add fixed version 1.1.1. by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/83


1.1.0 - 2021-12-16
------------------

## What's Changed
- Fix readme file by @zubrzubr in https://github.com/wagnerdelima/drf-social-oauth2/pull/43
- Reference the User model with get_user_model() by @bmpenuelas in https://github.com/wagnerdelima/drf-social-oauth2/pull/46
- Feat/django 4 support by @wagnerdelima in https://github.com/wagnerdelima/drf-social-oauth2/pull/82

## New Contributors
- @zubrzubr made their first contribution in https://github.com/wagnerdelima/drf-social-oauth2/pull/43
- @bmpenuelas made their first contribution in https://github.com/wagnerdelima/drf-social-oauth2/pull/46


1.0.9 - 2021-02-21
------------------

- Add general README info.
- JWT token provided through toggle.

1.0.6 - 2017-05-22
------------------

- Fix a bug where inactive users could still get tokens


1.0.5 - 2017-01-03
------------------

- Updated python-social-auth to social (`Migrating guide <https://github.com/omab/python-social-auth/blob/master/MIGRATING_TO_SOCIAL.md>`_)
- Wrapped token view and revoke token view in a rest framework APIView
- Added url namespace
- Renamed PROPRIETARY_BACKEND_NAME to DRFSO2_PROPRIETARY_BACKEND_NAME


1.0.2 - 2015-08-11
------------------

- Fix a bug where the hack to keep the django request was not working due to oauthlib encoding the object

1.0.1 - 2015-08-09
------------------

- Forgot to update django-oauth-toolkit version in setup.py (version 0.9.0 needed because of `this change <https://github.com/evonove/django-oauth-toolkit/commit/6bdee6d3a8c481dffaa68038cf3418b4f83c8f10>`_)

1.0.0 - 2015-07-30
------------------

- Convert token view api changed and is now more conform to the oauth2 api.
- Removed PROPRIETARY_BACKEND_NAME setting
- Invalidate sessions view now takes a client_id as a parameter
