"""
Tests for the createapp management command.

The command used to save the Application and print nothing — and since
django-oauth-toolkit hashes client secrets on save, the generated secret was
unrecoverable. It also crashed with a bare IndexError when no superuser
existed.
"""

from io import StringIO

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from oauth2_provider.models import Application
from pytest import fixture, raises, skip


@fixture(scope='function')
def superuser():
    admin = User.objects.create_superuser(
        username='createapp-admin',
        email='createapp-admin@email.com',
        password='password',
    )
    yield admin
    admin.delete()


def test_createapp_requires_a_superuser():
    # The suite runs against a shared, non-transactional database; only run
    # the no-superuser path when the precondition actually holds.
    if User.objects.filter(is_superuser=True).exists():
        skip('a superuser exists in the shared test database')
    with raises(CommandError, match='superuser'):
        call_command('createapp', name='doomed-app')
    assert not Application.objects.filter(name='doomed-app').exists()


def test_createapp_prints_credentials_once(superuser):
    out = StringIO()
    call_command('createapp', name='cmd-test-app', client_id='cmd-test-id', stdout=out)
    output = out.getvalue()

    try:
        application = Application.objects.get(client_id='cmd-test-id')
        assert application.name == 'cmd-test-app'
        assert application.user == superuser

        assert 'client_id: cmd-test-id' in output
        # The cleartext secret must be in the output: after save() only the
        # hash is stored, so this is the user's only chance to capture it.
        printed_secret = output.split('client_secret: ')[1].strip()
        assert printed_secret
        assert application.client_secret != printed_secret  # stored hashed
    finally:
        Application.objects.filter(client_id='cmd-test-id').delete()
