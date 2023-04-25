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
