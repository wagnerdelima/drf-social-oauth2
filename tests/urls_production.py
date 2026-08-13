"""URLconf mirroring the documented production wiring.

The installation docs tell users to mount this package under the ``drf``
namespace::

    path('auth/', include('drf_social_oauth2.urls', namespace='drf'))

which nests social_django's URLs as ``drf:social:...`` — the wiring that
exposed issues #79 and #244.
"""

from django.urls import include, path

urlpatterns = [
    path('auth/', include('drf_social_oauth2.urls', namespace='drf')),
]
