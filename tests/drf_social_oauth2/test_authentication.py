from django.http.request import HttpRequest
from pytest import raises
from rest_framework.exceptions import AuthenticationFailed

from drf_social_oauth2.authentication import SocialAuthentication


def create_request(content: str = 'Bearer'):
    request = HttpRequest()
    request.META = {'HTTP_AUTHORIZATION': content}
    request.session = None
    return request


def test_authenticate_no_auth_header_fail():
    authenticated = SocialAuthentication()
    assert not authenticated.authenticate(HttpRequest())


def test_authenticate_no_backend_fail():
    request = create_request('JWT')
    authenticated = SocialAuthentication()

    assert not authenticated.authenticate(request)


def test_authenticate_no_bearer_token_type():
    request = create_request('Bearer')
    authenticated = SocialAuthentication()

    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_empty_bearer_fail():
    request = create_request('Bearer facebook')
    authenticated = SocialAuthentication()

    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_wrongly_formatted_token_fail():
    token = 'Bearer facebook 401f7ac837da42b9 7f613d789819ff93537bee6a'
    request = create_request(token)
    authenticated = SocialAuthentication()

    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate(mocker):
    # A real HttpRequest: DRF >= 3.18 reads request.headers, which mocked
    # request classes don't populate from META.
    request = create_request('Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a')

    mocker.patch('drf_social_oauth2.authentication.load_backend')
    authenticated = SocialAuthentication()
    user, token = authenticated.authenticate(request)
    assert user
    assert token == '401f7ac837da42b97f613d789819ff93537bee6a'


def test_authenticate_missing_backend():
    token = 'Bearer unknown 401f7ac837da42b97f613d789819ff93537bee6a'
    request = create_request(token)

    authenticated = SocialAuthentication()
    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_user_not_found(mocker):
    request = create_request('Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a')

    load_backend_mocker = mocker.patch('drf_social_oauth2.authentication.load_backend')
    load_backend_mocker.return_value.do_auth.return_value = None

    authenticated = SocialAuthentication()
    with raises(AuthenticationFailed):
        authenticated.authenticate(request)


def test_authenticate_header():
    request = create_request('Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a')

    authenticated = SocialAuthentication()
    text = authenticated.authenticate_header(request)
    assert text == 'Bearer backend realm="api"'


def test_authenticate_inactive_user_fail(mocker):
    """A deactivated user's social token must not authenticate: the
    convert-token grant already rejected inactive users, but this per-request
    path did not."""
    request = create_request('Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a')

    load_backend_mocker = mocker.patch('drf_social_oauth2.authentication.load_backend')
    load_backend_mocker.return_value.do_auth.return_value.is_active = False

    authenticated = SocialAuthentication()
    with raises(AuthenticationFailed, match='inactive'):
        authenticated.authenticate(request)


def test_authenticate_provider_error_is_not_echoed(mocker):
    """Upstream provider response bodies are logged, not reflected to the
    caller."""
    from social_core.utils import requests

    request = create_request('Bearer facebook 401f7ac837da42b97f613d789819ff93537bee6a')

    provider_response = mocker.Mock(status_code=401, text='sensitive-upstream-details')
    load_backend_mocker = mocker.patch('drf_social_oauth2.authentication.load_backend')
    load_backend_mocker.return_value.do_auth.side_effect = requests.HTTPError(
        response=provider_response
    )

    authenticated = SocialAuthentication()
    with raises(AuthenticationFailed) as exc_info:
        authenticated.authenticate(request)

    assert 'sensitive-upstream-details' not in str(exc_info.value)
    assert 'HTTP 401' in str(exc_info.value)
