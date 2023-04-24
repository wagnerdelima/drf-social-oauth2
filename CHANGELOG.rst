Change log
==========

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
