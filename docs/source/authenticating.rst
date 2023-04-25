Authenticating Requests
=======================

One of the notable features of our framework is the default authentication backend, aptly named SocialAuthentication.
This backend facilitates a streamlined process of user registration and authentication with your REST API.

The class functions by retrieving the backend name and token from the Authorization header, and subsequently
authenticating the user through the relevant external provider. In the event that the user has not been previously
registered on your app, the backend creates a new user for this purpose, ensuring a seamless authentication process.


Authentication Ready View
-------------------------

You can set up a view which requires authentication just by inheriting from the generics class of Django Rest Framework,
as shown below:

.. code-block:: python

    from rest_framework import generics

    class MyView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        response = {
            'message': 'token works.'
        }
        return Response(response, status=200)

If, by any chance you need a view without authentication, just set the `authentication_class`

.. code-block:: python

    from rest_framework.permissions import AllowAny

    class MyView(generics.ListAPIView):
    authentication_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        response = {
            'message': 'token works.'
        }
        return Response(response, status=200)


Include the header `Authorization` to request, and your view should respond if your access token is valid:

.. code-block:: console

    $ curl -H "Authorization: Bearer <backend_name> <backend_token>" http://localhost:8000/route/to/your/view
