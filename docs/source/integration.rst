.. _integration:

Integration Social Backends
===========================

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

For each integration for every single backend, you need to add a new application for each corresponding social backend.
See the :ref:`new-application` section. This means that if you are authenticating with Facebook and Google, you
have to create two applications in the Application section in your Django Admin dashboard.

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

To test your REST API's settings, you can execute the following command:

.. code-block:: console

    $ curl -X POST -d "grant_type=convert_token&client_id=<client_id>&client_secret=<client_secret>&backend=facebook&token=<facebook_token>" http://localhost:8000/auth/convert-token

This command will return an `access_token` that you should use for every HTTP request to your API. The purpose of
this process is to convert a third-party access token (`user_access_token`) into an access token that you can use
with your API and its clients (`access_token`). By doing so, you will be able to authenticate each request and avoid
authenticating with Facebook every time.

You can obtain the ID (`SOCIAL_AUTH_FACEBOOK_KEY`) and secret (`SOCIAL_AUTH_FACEBOOK_SECRET`) of your app from
https://developers.facebook.com/apps/.

For testing purposes, you can utilize the access token `user_access_token` from https://developers.facebook.com/tools/accesstoken/.

If you require further information on how to configure python-social-auth with Facebook,
visit http://python-social-auth.readthedocs.io/en/latest/backends/facebook.html.


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

To test the configuration settings, execute the following command:

.. code-block:: console

    $ curl -X POST -d "grant_type=convert_token&client_id=<django-oauth-generated-client_id>&client_secret=<django-oauth-generated-client_secret>&backend=google-oauth2&token=<google_token>" http://localhost:8000/auth/convert-token

Upon successful execution, the above command returns an `access_token` that you must utilize for each HTTP request made
to your REST API. In essence, what is happening here is that you are converting a third-party access token
(`user_access_token`) into an access token that can be used with your API and its clients (`access_token`).
For each subsequent communication between your system/application and your API, it is necessary to use this
token to authenticate each request, thereby avoiding the need to authenticate with Google every time.

To obtain your app's ID (`SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`) and secret (`SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`), visit https://console.developers.google.com/apis/credentials.
For more details on how to create an ID and secret, visit https://developers.google.com/identity/protocols/OAuth2.

For testing purposes, you can use the access token `user_access_token` from
https://developers.google.com/oauthplayground/ and follow these steps:

    - Visit the OAuth 2.0 Playground
    - Select Google OAuth2 API v2 and authorize for https://www.googleapis.com/auth/userinfo.email and https://www.googleapis.com/auth/userinfo.profile
    - Exchange Authorization code for tokens and get access token
    - Use the access token as the token parameter in the /convert-token endpoint.

For more information on configuring python-social-auth with Google, please visit https://python-social-auth.readthedocs.io/en/latest/backends/google.html#google-oauth2.

Should you prefer a step-by-step tutorial, refer to this link provided by @djangokatya: https://djangokatya.com/2021/04/09/social-login-for-django-rest-framefork-for-newbies-a-k-a-for-me/.


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

For testing purposes, you can use the id token `id_token` from
https://developers.google.com/oauthplayground/.

    1. Visit the OAuth 2.0 Playground.
    2. Select Google OAuth2 API v2 and authorize for openid.
    3. Exchange Authorization code for tokens and get access token.
    4. Use the access token as the token parameter in the /convert-token endpoint.

If you want to have your open id token validated, copy it and hit this url,
https://oauth2.googleapis.com/tokeninfo?id_token=your_token_here.

To test the configuration settings, execute the following command:

.. code-block:: console

    $ curl -X POST -d "grant_type=convert_token&client_id=<django-oauth-generated-client_id>&client_secret=<django-oauth-generated-client_secret>&backend=google-identity&token=<google_openid_token>" http://localhost:8000/auth/convert-token


Github Integration
^^^^^^^^^^^^^^^^^^

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

You need to register a new GitHub app at https://github.com/settings/applications/new. set the callback URL to
http://example.com/complete/github/ replacing example.com with your domain.

The Client ID should be added on SOCIAL_AUTH_GITHUB_KEY and the `SOCIAL_AUTH_GITHUB_KEY` should be added on
`SOCIAL_AUTH_GITHUB_SECRET`.

Now, visit https://github.com/settings/tokens and create a new token. Select the user checkbox, as to grant user access.
The click on the Generate Token button. Use the access token as the token parameter in the /convert-token endpoint.

Other Backend Integration
^^^^^^^^^^^^^^^^^^^^^^^^^

DRF-Social-Oauth2 is not only limited to Google, Facebook and Github. You can integrate with every backend described
at the Python Social Oauth backend integrations.
