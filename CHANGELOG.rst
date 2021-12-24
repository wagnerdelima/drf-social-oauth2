Change log
==========

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
