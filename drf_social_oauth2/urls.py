try:
    from django.conf.urls import url, include

except ImportError:
    from django.urls import re_path, include

from django.urls import path

from oauth2_provider.views import AuthorizationView
from social_django.views import complete

from drf_social_oauth2.views import (
    ConvertTokenView,
    TokenView,
    RevokeTokenView,
    invalidate_sessions,
    DisconnectBackendView,
)

app_name = 'drfso2'


urlpatterns = [path('complete/<str:backend>/', complete, name='complete')]

try:
    urlpatterns += [
        url(r'^authorize/?$', AuthorizationView.as_view(), name='authorize'),
        url(r'^token/?$', TokenView.as_view(), name='token'),
        url('', include('social_django.urls', namespace='social')),
        url(r'^convert-token/?$', ConvertTokenView.as_view(), name='convert_token'),
        url(r'^revoke-token/?$', RevokeTokenView.as_view(), name='revoke_token'),
        url(
            r'^invalidate-sessions/?$', invalidate_sessions, name='invalidate_sessions'
        ),
        url(
            r'^disconnect-backend/?$',
            DisconnectBackendView.as_view(),
            name='disconnect_backend',
        ),
    ]
except NameError:
    urlpatterns += [
        re_path(r'^authorize/?$', AuthorizationView.as_view(), name='authorize'),
        re_path(r'^token/?$', TokenView.as_view(), name='token'),
        re_path('', include('social_django.urls', namespace='social')),
        re_path(r'^convert-token/?$', ConvertTokenView.as_view(), name='convert_token'),
        re_path(r'^revoke-token/?$', RevokeTokenView.as_view(), name='revoke_token'),
        re_path(
            r'^invalidate-sessions/?$', invalidate_sessions, name='invalidate_sessions'
        ),
        re_path(
            r'^disconnect-backend/?$',
            DisconnectBackendView.as_view(),
            name='disconnect_backend',
        ),
    ]
