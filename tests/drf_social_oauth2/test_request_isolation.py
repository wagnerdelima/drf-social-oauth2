"""
Tests for SocialTokenServer's per-request isolation of the Django request.

django-oauth-toolkit caches its oauthlib core — and with it the
SocialTokenServer — per view class, so one server instance is shared by every
request in the process. The Django request used to be stored on the instance,
letting concurrent requests swap or steal each other's value; it now lives in
a ContextVar, which is isolated per thread/async context.
"""

import threading

from django.http import HttpRequest
from pytest import raises

from drf_social_oauth2.oauth2_endpoints import SocialTokenServer


def make_server(mocker) -> SocialTokenServer:
    return SocialTokenServer(request_validator=mocker.Mock())


def test_set_and_pop_round_trip(mocker):
    server = make_server(mocker)
    request = HttpRequest()

    server.set_request_object(request)
    assert server.pop_request_object() is request
    # Popping consumes the value.
    assert server.pop_request_object() is None


def test_set_rejects_non_django_request(mocker):
    server = make_server(mocker)
    with raises(TypeError):
        server.set_request_object(object())


def test_request_is_not_visible_across_threads(mocker):
    """A request stored while serving one request must never be observable
    from another thread — that would hand user A's session to user B."""
    server = make_server(mocker)
    server.set_request_object(HttpRequest())

    seen_in_other_thread = []

    def other_thread():
        seen_in_other_thread.append(server.pop_request_object())

    thread = threading.Thread(target=other_thread)
    thread.start()
    thread.join()

    assert seen_in_other_thread == [None]
    # Our own value is untouched by the other thread's pop.
    assert server.pop_request_object() is not None


def test_concurrent_threads_each_get_their_own_request(mocker):
    """Interleaved set/pop across threads must never swap request objects.
    With instance-level storage, the barrier below made thread A pop thread
    B's request."""
    server = make_server(mocker)
    barrier = threading.Barrier(2)
    results: dict[str, HttpRequest | None] = {}

    def worker(name: str):
        request = HttpRequest()
        request._marker = name
        server.set_request_object(request)
        barrier.wait()  # both threads have now called set_request_object
        results[name] = server.pop_request_object()

    threads = [threading.Thread(target=worker, args=(n,)) for n in ('a', 'b')]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results['a']._marker == 'a'
    assert results['b']._marker == 'b'
