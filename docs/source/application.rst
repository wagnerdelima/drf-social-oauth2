.. _new-application:

Setting Up a New Application
============================

To begin, navigate to the Django admin panel and create a new application with the following configuration:

- Leave the `client_id` and `client_secret` fields unchanged.
- Set the `user` field to your superuser.
- Leave the `redirect_uris` field blank.
- Set the `client_type` field to confidential.
- Set the `authorization_grant_type` field to 'Resource owner password-based'.
- Optionally, you can set the `name` field to a name of your choice.

With these settings in place, the installation is now complete and you can proceed to test the newly configured application.

For further information and to take full advantage of the capabilities of this package, it is highly recommended
that you refer to the documentation for python-social-auth and django-oauth-toolkit.
If you intend to enable a social backend such as Facebook, you may want to consult the python-social-auth
documentation on `supported backends <http://python-social-auth.readthedocs.io/en/latest/backends/index.html#supported-backends>`_
and the django-social-auth documentation on `backend configuration <http://python-social-auth.readthedocs.io/en/latest/configuration/django.html>`_.


Screenshot of the new application creation.

.. image:: new_application.png
  :class: png
  :width: 1200
  :alt: Adding a new application to your drf-social-oauth2 installation.

Your new application shows a "Hash client secret" checkbox. Since version
3.5.0 you can leave it enabled (django-oauth-toolkit's default): the
convert-token and revoke-token endpoints authenticate the application
server-side and work with hashed secrets. Earlier releases required the
checkbox to be disabled — if you unchecked it back then, it is safe to
re-enable now.

Note that, this new version of drf-social-oauth2 does not require the client_secret to be passed on the HTTPs requests.

Please, read the :ref:`integration` in order to integrate social libraries into your project.
