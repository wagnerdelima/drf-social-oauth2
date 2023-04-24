DRF Social OAuth2
===================================

.. image:: https://badge.fury.io/py/drf-social-oauth2.svg
    :target: https://badge.fury.io/for/py/drf-social-oauth2

.. image:: https://www.codefactor.io/repository/github/wagnerdelima/drf-social-oauth2/badge
    :target: https://www.codefactor.io/repository/github/wagnerdelima/drf-social-oauth2/badge


Introduction
^^^^^^^^^^^^

This module provides OAuth2 social authentication support for applications in Django REST Framework.

The aim of this package is to help set up social authentication for your REST API. It also helps setting up your OAuth2
provider.

This package relies on `python-social-auth <http://python-social-auth.readthedocs.io>`_ and
`django-oauth-toolkit <https://django-oauth-toolkit.readthedocs.org>`_.
You should probably read their docs if you were to go further than what is done here.
If you have some hard time understanding OAuth2, you can read a simple explanation
`here <https://aaronparecki.com/articles/2012/07/29/1/oauth2-simplified>`_.

If you would like to test out this framework but you do not want to spend time at setting it up
in your local environment, you can visit my `facebook_setup <https://github.com/wagnerdelima/facebook_setup>`_ repo.
It contains all the configuration necessary for you to try. It's missing database configuration, however
all you have to do is set up a database in the settings.py file.

Installation
------------

This framework is published at the PyPI, install it with pip::

    pip install drf_social_oauth2


Add the following to your ``INSTALLED_APPS``:

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

For versions of Django 4.0 or higher, use:

.. code-block:: python

    from django.urls import re_path

    urlpatterns = patterns(
        ...
        re_path(r'^auth/', include('drf_social_oauth2.urls', namespace='drf'))
    )

Add these context processors to your ``TEMPLATE_CONTEXT_PROCESSORS``:

.. code-block:: python

    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'social_django.context_processors.backends',
        'social_django.context_processors.login_redirect',
    )

NB: since Django version 1.8, the ``TEMPLATE_CONTEXT_PROCESSORS`` is deprecated, set the ``'context_processors'`` option
in the ``'OPTIONS'`` of a DjangoTemplates backend instead:

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


You can then enable the authentication classes for Django REST Framework by default or per view (add or update the
``REST_FRAMEWORK`` and ``AUTHENTICATION_BACKENDS`` entries in your settings.py)

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


The settings of this  app are:

- ``DRFSO2_PROPRIETARY_BACKEND_NAME``: name of your OAuth2 social backend (e.g ``"Facebook"``), defaults to ``"Django"``
- ``DRFSO2_URL_NAMESPACE``: namespace for reversing URLs
- ``ACTIVATE_JWT``: If set to True the access and refresh tokens will be JWTed. Default is False.

Setting Up a New Application
----------------------------

Go to Django admin and add a new Application with the following configuration:

- ``client_id`` and ``client_secret`` should be left unchanged
- ``user`` should be your superuser
- ``redirect_uris`` should be left blank
- ``client_type`` should be set to ``confidential``
- ``authorization_grant_type`` should be set to ``'Resource owner password-based'``
- ``name`` can be set to whatever you'd like

The installation is done, you can now test the newly configured application.

It is recommended that you read the docs from `python-social-auth` and `django-oauth-toolkit` if you would like to go
further. If you want to enable a social backend (e.g. Facebook), check the docs of `python-social-auth` on
`supported backends <http://python-social-auth.readthedocs.io/en/latest/backends/index.html#supported-backends>`_
and `django-social-auth` on `backend configuration <http://python-social-auth.readthedocs.io/en/latest/configuration/django.html>`_.


Testing the Setup
-----------------

Now that the installation is done, let's try out the various functionality.
We will assume for the following examples that the REST API is reachable on ``http://localhost:8000``.

- Retrieve a token for a user using ``curl``::

    curl -X POST -d "client_id=<client_id>&client_secret=<client_secret>&grant_type=password&username=<user_name>&password=<password>" http://localhost:8000/auth/token

``<client_id>`` and ``<client_secret>`` are the keys generated automatically. you can find in the model Application you created.

-  Refresh token::

    curl -X POST -d "grant_type=refresh_token&client_id=<client_id>&client_secret=<client_secret>&refresh_token=<your_refresh_token>" http://localhost:8000/auth/token

- Exchange an external token for a token linked to your app::

    curl -X POST -d "grant_type=convert_token&client_id=<client_id>&client_secret=<client_secret>&backend=<backend>&token=<backend_token>" http://localhost:8000/auth/convert-token

``<backend>`` here needs to be replaced by the name of an enabled backend (e.g. "Facebook"). Note that ``PROPRIETARY_BACKEND_NAME``
is a valid backend name, but there is no use to do that here.
``<backend_token>`` is for the token you got from the service utilizing an iOS app for example.

- Revoke tokens:

    Revoke a single token::

        curl -X POST -d "client_id=<client_id>&client_secret=<client_secret>&token=<your_token>" http://localhost:8000/auth/revoke-token

    Revoke all tokens for a user::

        curl -H "Authorization: Bearer <token>" -X POST -d "client_id=<client_id>" http://localhost:8000/auth/invalidate-sessions

    Revoke only refresh tokens::

        curl -H "Authorization: Bearer <token>" -X POST -d "client_id=<client_id>" http://localhost:8000/auth/invalidate-refresh-tokens


Authenticating Requests
-----------------------

As you have probably noticed, we enabled a default authentication backend called ``SocialAuthentication``.
This backend lets you register and authenticate your users seamlessly with your REST API.

The class simply retrieves the backend name and token from the Authorization header and tries to authenticate the user
using the corresponding external provider. If the user was not yet registered on your app, it will automatically create
a new user for this purpose.

Example authenticated request::

    curl -H "Authorization: Bearer <backend_name> <backend_token>" http://localhost:8000/route/to/your/view


Integration Examples
--------------------

For each authentication provider, the top portion of your REST API settings.py file should look like this:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        # OAuth
        'oauth2_provider',
        'social_django',
        'drf_social_oauth2',
    )

    TEMPLATES = [
        {
            ...
            'OPTIONS': {
                'context_processors': [
                    ...
                    # OAuth
                    'social_django.context_processors.backends',
                    'social_django.context_processors.login_redirect',
                ],
            },
        }
    ]

    REST_FRAMEWORK = {
        ...
        'DEFAULT_AUTHENTICATION_CLASSES': (
            ...
            # OAuth
            # 'oauth2_provider.ext.rest_framework.OAuth2Authentication',  # django-oauth-toolkit < 1.0.0
            'oauth2_provider.contrib.rest_framework.OAuth2Authentication',  # django-oauth-toolkit >= 1.0.0
            'drf_social_oauth2.authentication.SocialAuthentication',
        )
    }

Listed below are a few examples of supported backends that can be used for social authentication.


Facebook Integration
^^^^^^^^^^^^^^^^^^^^

To use Facebook as the authorization backend of your REST API, your settings.py file should look like this:

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # Others auth providers (e.g. Google, OpenId, etc)
        ...

        # Facebook OAuth2
        'social_core.backends.facebook.FacebookAppOAuth2',
        'social_core.backends.facebook.FacebookOAuth2',

        # drf_social_oauth2
        'drf_social_oauth2.backends.DjangoOAuth2',

        # Django
        'django.contrib.auth.backends.ModelBackend',
    )

    # Facebook configuration
    SOCIAL_AUTH_FACEBOOK_KEY = '<your app id goes here>'
    SOCIAL_AUTH_FACEBOOK_SECRET = '<your app secret goes here>'

    # Define SOCIAL_AUTH_FACEBOOK_SCOPE to get extra permissions from Facebook.
    # Email is not sent by default, to get it, you must request the email permission.
    SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
    SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
        'fields': 'id, name, email'
    }

Remember to add this new Application in your Django admin (see section "Setting up Application").

You can test these settings by running the following command::

    curl -X POST -d "grant_type=convert_token&client_id=<client_id>&client_secret=<client_secret>&backend=facebook&token=<facebook_token>" http://localhost:8000/auth/convert-token

This request returns the "access_token" that you should use with every HTTP request to your REST API. What is happening
here is that we are converting a third-party access token (``<user_access_token>``) to an access token to use with your
API and its clients ("access_token"). You should use this token on each and further communications between your
system/application and your api to authenticate each request and avoid authenticating with Facebook every time.

You can get the ID (``SOCIAL_AUTH_FACEBOOK_KEY``) and secret (``SOCIAL_AUTH_FACEBOOK_SECRET``) of your app at
https://developers.facebook.com/apps/.

For testing purposes, you can use the access token ``<user_access_token>`` from https://developers.facebook.com/tools/accesstoken/.

For more information on how to configure python-social-auth with Facebook visit
http://python-social-auth.readthedocs.io/en/latest/backends/facebook.html.


Google Integration
^^^^^^^^^^^^^^^^^^

To use Google OAuth2 as the authorization backend of your REST API, your settings.py file should look like this:

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # Others auth providers (e.g. Facebook, OpenId, etc)
        ...
        # Google  OAuth2
        'social_core.backends.google.GoogleOAuth2',
        # drf-social-oauth2
        'drf_social_oauth2.backends.DjangoOAuth2',
        # Django
        'django.contrib.auth.backends.ModelBackend',
    )

    # Google configuration
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = <your app id goes here>
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = <your app secret goes here>

    # Define SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE to get extra permissions from Google.
    SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
    ]

Remember to add the new Application in your Django admin (see section "Setting up Application").

You can test these settings by running the following command::

    curl -X POST -d "grant_type=convert_token&client_id=<django-oauth-generated-client_id>&client_secret=<django-oauth-generated-client_secret>&backend=google-oauth2&token=<google_token>" http://localhost:8000/auth/convert-token

This request returns an "access_token" that you should use with every HTTP requests to your REST API.
What is happening here is that we are converting a third-party access token (``<user_access_token>``)
to an access token to use with your API and its clients ("access_token"). You should use this token on
each and further communications between your system/application and your API to authenticate each request
and avoid authenticating with Google every time.

You can get the ID (``SOCIAL_AUTH_GOOGLE_OAUTH2_KEY``) and secret (``SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET``)
of your app at https://console.developers.google.com/apis/credentials
and more information on how to create one on https://developers.google.com/identity/protocols/OAuth2.

In the Google API Credential, create a new "Oauth Client ID". Once it's created, Google will show you a Client ID and
a Client Secret. Use the Client ID at ``SOCIAL_AUTH_GOOGLE_OAUTH2_KEY``, and the Client Secret at
``SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET``.

For testing purposes, you can use the access token ``<user_access_token>`` from
https://developers.google.com/oauthplayground/.

    1. Visit the OAuth 2.0 Playground
    2. Select Google OAuth2 API v2 and authorize for https://www.googleapis.com/auth/userinfo.email and https://www.googleapis.com/auth/userinfo.profile
    3. Exchange Authorization code for tokens and get access token
    4. Use the access token as the token parameter in the /convert-token endpoint.

If you would like a step-by-step tutorial, see this link, by @djangokatya:
https://djangokatya.com/2021/04/09/social-login-for-django-rest-framefork-for-newbies-a-k-a-for-me/

For more information on how to configure python-social-auth with Google visit
https://python-social-auth.readthedocs.io/en/latest/backends/google.html#google-oauth2.


Google OpenID Integration
^^^^^^^^^^^^^^^^^^^^^^^^^

OpenID and access tokens are two different concepts that are used in authentication and authorization systems.

OpenID is an open standard that allows users to authenticate with multiple websites and applications using a single
set of credentials. When a user logs in using OpenID, they are redirected to their OpenID provider, which authenticates
them and provides the website or application with a unique identifier for the user. The identifier can be used to
retrieve the user's profile information, but it does not provide any authorization to access APIs or services.

Access tokens, on the other hand, are used to authorize API requests on behalf of the user.
When a user logs in and grants permission to access their data, an access token is generated and returned to the client
application. The access token is used to authenticate the client application and authorize it to make API requests on
behalf of the user. The access token contains information such as the permissions granted to the client application,
the expiration time, and a signature that verifies the token's authenticity.

In summary, OpenID is used to authenticate users and provide a unique identifier for them, while access tokens are
used to authorize API requests on behalf of the user. While OpenID and access tokens are both important components
of authentication and authorization systems, they serve different purposes and should not be confused with each other.

In order to authenticate with Open ID, proceed as follows:


.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # Others auth providers (e.g. Facebook, OpenId, etc)
        ...
        # Google  OAuth2
        'drf_social_oauth2.backends.GoogleIdentityBackend',
        # drf-social-oauth2
        'drf_social_oauth2.backends.DjangoOAuth2',
        # Django
        'django.contrib.auth.backends.ModelBackend',
    )

    # Google configuration
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = <your app id goes here>
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = <your app secret goes here>

    # Define SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE to get extra permissions from Google.
    SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
    ]


For testing purposes, you can use the id token ``<id_token>`` from
https://developers.google.com/oauthplayground/.

    1. Visit the OAuth 2.0 Playground.
    2. Select Google OAuth2 API v2 and authorize for openid.
    3. Exchange Authorization code for tokens and get access token.
    4. Use the access token as the token parameter in the /convert-token endpoint.

If you want to have your open id token validated, copy it and hit this url,
https://oauth2.googleapis.com/tokeninfo?id_token=your_token_here.

You can test these settings by running the following command::

    curl -X POST -d "grant_type=convert_token&client_id=<django-oauth-generated-client_id>&client_secret=<django-oauth-generated-client_secret>&backend=google-identity&token=<google_openid_token>" http://localhost:8000/auth/convert-token

^^^^^^^^^^^^^^

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        # Others auth providers (e.g. Facebook, OpenId, etc)
        ...

        # GitHub OAuth2
        'social_core.backends.github.GithubOAuth2',

        # drf-social-oauth2
        'drf_social_oauth2.backends.DjangoOAuth2',

        # Django
        'django.contrib.auth.backends.ModelBackend',
    )

    # Google configuration
    SOCIAL_AUTH_GITHUB_KEY = <your app id goes here>
    SOCIAL_AUTH_GITHUB_SECRET = <your app secret goes here>

Remember to add the new Application in your Django admin (see section "Setting up Application"), just for GitHub.

You need to register a new GitHub app at https://github.com/settings/applications/new. set the callback URL to
http://example.com/complete/github/ replacing example.com with your domain.

The Client ID should be added on SOCIAL_AUTH_GITHUB_KEY and the ``SOCIAL_AUTH_GITHUB_KEY`` should be added on
``SOCIAL_AUTH_GITHUB_SECRET``.

Now, visit https://github.com/settings/tokens and create a new token. Select the user checkbox, as to grant user access.
The click on the Generate Token button. Use the access token as the token parameter in the /convert-token endpoint.

Running local tests
^^^^^^^^^^^^^^^^^^^

You may find drf-social-oauth2's unit tests in the tests/ directory. In order to run the tests locally, you need to
build the docker image and execute the test run command with the following commands below:


    $ docker-compose -f docker-compose.tests.yml build --no-cache
    $ docker-compose -f docker-compose.tests.yml up --exit-code-from app

Then, destroy all containers created in your local system:

    $ docker-compose -f docker-compose.tests.yml down

Your local environment has a htmlcov/ folder with the test coverage. See the index.html file for more info about the
coverage of the project.


Customize token expiration
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can set the expiry time for tokens as follows:

.. code-block:: python

    # in your settings.py file.
    from oauth2_provider import settings as oauth2_settings

    # expires in 6 months
    oauth2_settings.DEFAULTS['ACCESS_TOKEN_EXPIRE_SECONDS'] = 1.577e7

Run Swagger Editor
^^^^^^^^^^^^^^^^^^

Run the Swagger Editor's and interact with the API:

On Mac and Linux:

    $ docker run --rm -p 8080:8080 -v $(pwd):/tmp -e SWAGGER_FILE=/tmp/api.yaml swaggerapi/swagger-editor

On Windows:

    $ docker run --rm -p 8080:8080 -v ${pwd}:/tmp -e SWAGGER_FILE=/tmp/api.yaml swaggerapi/swagger-editor


What Am I Working Next?
^^^^^^^^^^^^^^^^^^^^^^^

I will be working on the issues below. Anyone is welcome to contribute.

    - Investigating Issues.
