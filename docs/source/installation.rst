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

   $ pip install drf_social_oauth2==2.1.3


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
- ``ACTIVATE_JWT``: If set to True the access and refresh tokens will be JWTed. Default is False.
