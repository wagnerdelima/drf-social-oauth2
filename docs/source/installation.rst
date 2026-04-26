Usage
=====

This guide will walk you through the process of installing DRF-Social-OAuth2 and setting it up for use with
your Django REST Framework application. It assumes that you have some familiarity with Django and have a basic
understanding of OAuth2 authentication. If you're new to Django or OAuth2, we recommend checking out our resources
section for additional learning materials.

To begin, you'll need to have Python 3 and pip installed on your local machine. Once you have those installed,
you can follow the instructions outlined in the installation section of this guide to install DRF-Social-OAuth2 and
its dependencies. Then, you can configure your Django settings to use DRF-Social-OAuth2 by adding the necessary lines to
your settings.py file. Finally, you'll need to migrate your database to apply the changes.

By the end of this guide, you'll have successfully installed DRF-Social-OAuth2 and set it up for use with your
Django REST Framework application. With DRF-Social-OAuth2, you can make your REST API more secure and user-friendly
by allowing users to authenticate with their social media accounts.


Installation
------------

This framework is published at the PyPI, install it with pip:

.. code-block:: console

   $ pip install drf_social_oauth2==3.1.0


To enable OAuth2 social authentication support for your Django REST Framework application, you need to install
and configure drf-social-oauth2. To get started, add the following packages to your INSTALLED_APPS:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'oauth2_provider',
        'social_django',
        'drf_social_oauth2',
    )


Include social auth urls to your urls.py:

.. code-block:: python

    from django.conf.urls import url

    urlpatterns = patterns(
        ...
        url(r'^auth/', include('drf_social_oauth2.urls', namespace='drf'))
    )

For versions of Django 4.0 or higher, use `re_path` instead:

.. code-block:: python

    from django.urls import re_path

    urlpatterns = patterns(
        ...
        re_path(r'^auth/', include('drf_social_oauth2.urls', namespace='drf'))
    )

Next, add the following context processors to your TEMPLATE_CONTEXT_PROCESSORS:

.. code-block:: python

    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'social_django.context_processors.backends',
        'social_django.context_processors.login_redirect',
    )


Note that since Django version 1.8, the TEMPLATE_CONTEXT_PROCESSORS setting is deprecated. You should instead
set the 'context_processors' option in the OPTIONS of a DjangoTemplates backend:

.. code-block:: python

    TEMPLATES = [
        {
            ...
            'OPTIONS': {
                'context_processors': [
                    ...
                    'social_django.context_processors.backends',
                    'social_django.context_processors.login_redirect',
                ],
            },
        }
    ]

You can then enable the authentication classes for Django REST Framework by default or per view by updating
the REST_FRAMEWORK and AUTHENTICATION_BACKENDS entries in your settings.py:

.. code-block:: python

    REST_FRAMEWORK = {
        ...
        'DEFAULT_AUTHENTICATION_CLASSES': (
            ...
            # 'oauth2_provider.ext.rest_framework.OAuth2Authentication',  # django-oauth-toolkit < 1.0.0
            'oauth2_provider.contrib.rest_framework.OAuth2Authentication',  # django-oauth-toolkit >= 1.0.0
            'drf_social_oauth2.authentication.SocialAuthentication',
        ),
    }

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        ...
       'drf_social_oauth2.backends.DjangoOAuth2',
       'django.contrib.auth.backends.ModelBackend',
    )

The following are settings available for drf-social-oauth2:

- ``DRFSO2_PROPRIETARY_BACKEND_NAME``: name of your OAuth2 social backend (e.g ``"Facebook"``), defaults to ``"Django"``
- ``DRFSO2_URL_NAMESPACE``: namespace for reversing URLs
- ``ACTIVATE_JWT``: if set to True, both access and refresh tokens are issued as JWTs signed with ``SECRET_KEY`` (HS256). Default is False. See `Activating JWT tokens`_ below.


Activating JWT tokens
---------------------

To make ``/auth/token`` and ``/auth/convert-token`` issue JWT-encoded access and
refresh tokens, set ``ACTIVATE_JWT = True`` in your Django settings:

.. code-block:: python

    # settings.py
    ACTIVATE_JWT = True

That is the only thing you need to do — provided ``'drf_social_oauth2'`` is in
``INSTALLED_APPS``, the package's ``AppConfig.ready()`` hook wires the JWT
generators into django-oauth-toolkit at startup.

**What the response looks like**

The ``token_type`` field stays ``"Bearer"`` — that is the OAuth2 transport, not
the token format. The JWT lives in the ``access_token`` (and ``refresh_token``)
value itself: three dot-separated base64url segments.

.. code-block:: json

    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6Ii4uLiJ9.SIGNATURE",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "read write",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6Ii4uLiJ9.SIGNATURE"
    }

You can verify the token format with PyJWT:

.. code-block:: python

    import jwt
    from django.conf import settings

    decoded = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
    # {'token': '<random 30-char opaque token>'}

**Using the token in subsequent requests**

Send it as a normal Bearer credential:

.. code-block:: text

    Authorization: Bearer eyJhbGciOi...

Do **not** include the backend name in the header (e.g. ``Bearer facebook eyJ...``);
that format is rejected by ``OAuth2Authentication``.

**Caveat: explicit overrides win**

If your ``OAUTH2_PROVIDER`` dict explicitly sets ``ACCESS_TOKEN_GENERATOR`` or
``REFRESH_TOKEN_GENERATOR``, those values take precedence and ``ACTIVATE_JWT``
becomes a no-op. Either remove those keys or point them at
``'drf_social_oauth2.generate_token'`` yourself.
