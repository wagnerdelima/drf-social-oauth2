"""
OAuth2 request validators for drf-social-oauth2.
"""

from django.utils.crypto import constant_time_compare
from oauth2_provider.settings import oauth2_settings


class SocialTokenValidator(oauth2_settings.OAUTH2_VALIDATOR_CLASS):
    """Request validator for endpoints where this package injects the secret.

    ``ConvertTokenView`` and ``RevokeTokenView`` deliberately do not require
    clients to send ``client_secret``: the view reads the Application's stored
    ``client_secret`` from the database and injects it into the request before
    handing it to oauthlib. That worked while django-oauth-toolkit stored
    secrets in cleartext, but DOT >= 2.3 hashes ``client_secret`` on save, so
    the injected value is the *hash* — and the stock validator hashes whatever
    the request presents before comparing, which can never match. The result
    was that every convert-token/revoke-token call against an application with
    a hashed secret failed with ``invalid_client`` (the docs used to tell
    users to disable the "Hash client secret" checkbox as a workaround).

    This validator additionally accepts a presented secret that is byte-equal
    to the stored value. Security considerations:

    - It does not weaken these endpoints: the compared value is injected
      server-side from the database; it never has to be known by — and is
      never revealed to — the client. Client authentication on these
      endpoints was already nominal for exactly that reason (possession of
      the social provider token is the credential that matters).
    - A real cleartext secret still validates through the parent class, so
      clients that do send their secret keep working.
    - Do not use this validator for grants where the client is expected to
      prove knowledge of the secret (e.g. the password grant on
      ``TokenView``): there, accepting the stored value verbatim would let a
      leaked hash be replayed. Those views keep the stock validator.
    """

    def _check_secret(self, provided_secret, stored_secret) -> bool:
        if super()._check_secret(provided_secret, stored_secret):
            return True
        return bool(provided_secret) and constant_time_compare(
            str(provided_secret), str(stored_secret)
        )
