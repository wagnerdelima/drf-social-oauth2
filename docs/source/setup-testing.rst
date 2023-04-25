Testing the Setup
=================

Welcome to the installation guide. Now that you have completed the installation, let's explore the various functionalities
provided by this package. For the following examples, we will assume that the REST API is reachable at http://localhost:8000.

To retrieve a token for a user, you can use the following command with curl:

.. code-block:: console

    $ curl -X POST -d "client_id=<client_id>&client_secret=<client_secret>&grant_type=password&username=<user_name>&password=<password>" http://localhost:8000/auth/token

Here, replace `client_id` and `client_secret` with the keys generated automatically by the Application model you created.

To refresh a token, use the following command:

.. code-block:: console

    $ curl -X POST -d "grant_type=refresh_token&client_id=<client_id>&client_secret=<client_secret>&refresh_token=<your_refresh_token>" http://localhost:8000/auth/token

You can exchange an external token for a token linked to your app using:

.. code-block:: console

    $ curl -X POST -d "grant_type=convert_token&client_id=<client_id>&client_secret=<client_secret>&backend=<backend>&token=<backend_token>" http://localhost:8000/auth/convert-token

Here, replace `backend` with the name of an enabled backend and `backend_token` with the token you received from the external service.

Finally, to revoke tokens, use the following commands:

To revoke a single token:

.. code-block:: console

    $ curl -X POST -d "client_id=<client_id>&client_secret=<client_secret>&token=<your_token>" http://localhost:8000/auth/revoke-token

To revoke all tokens for a user:

.. code-block:: console

    $ curl -H "Authorization: Bearer <token>" -X POST -d "client_id=<client_id>" http://localhost:8000/auth/invalidate-sessions

To revoke only refresh tokens:

.. code-block:: console

    $ curl -H "Authorization: Bearer <token>" -X POST -d "client_id=<client_id>" http://localhost:8000/auth/invalidate-refresh-tokens

No need to build your own request as you can also use the provided curl commands or the Swagger interface.
