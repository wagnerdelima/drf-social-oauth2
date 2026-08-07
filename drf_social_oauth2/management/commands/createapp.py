from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from oauth2_provider.generators import generate_client_id, generate_client_secret
from oauth2_provider.models import Application

User = get_user_model()


class Command(BaseCommand):
    help = "Create a Django OAuth Toolkit application (an existing admin is required)"

    def add_arguments(self, parser):
        parser.add_argument(
            "-ci", "--client_id", help="Client ID (recommended 40 characters long)"
        )
        parser.add_argument(
            "-cs",
            "--client_secret",
            help="Client Secret (recommended 128 characters long)",
        )
        parser.add_argument("-n", "--name", help="Name for the application")

    def handle(self, *args, **options):
        owner = User.objects.filter(is_superuser=True).first()
        if owner is None:
            raise CommandError(
                'No superuser found. Create one first (python manage.py '
                'createsuperuser) so the application has an owner.'
            )

        client_id = options["client_id"] or generate_client_id()
        client_secret = options["client_secret"] or generate_client_secret()

        new_application = Application(
            user=owner,
            client_type="confidential",
            authorization_grant_type="password",
            name=options["name"] or "socialauth_application",
            client_id=client_id,
            client_secret=client_secret,
        )
        new_application.save()

        self.stdout.write(
            self.style.SUCCESS(f'Application "{new_application.name}" created.')
        )
        self.stdout.write(f'client_id: {client_id}')
        # django-oauth-toolkit hashes the secret on save, so this is the only
        # chance to read it back.
        self.stdout.write(f'client_secret: {client_secret}')
