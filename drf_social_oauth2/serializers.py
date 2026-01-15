"""
Serializers for drf-social-oauth2 API endpoints.

This module provides serializers for validating request data
in OAuth2 token operations.
"""

from rest_framework.serializers import CharField, IntegerField, Serializer


class InvalidateRefreshTokenSerializer(Serializer):
    """Serializer for invalidating refresh tokens.

    Validates the client_id parameter required for identifying
    which application's refresh tokens to invalidate.
    """

    client_id = CharField(
        max_length=200,
        help_text="The OAuth2 application client ID.",
        error_messages={
            'required': 'client_id is required.',
            'blank': 'client_id cannot be blank.',
        }
    )


class InvalidateSessionsSerializer(Serializer):
    """Serializer for invalidating user sessions (access tokens).

    Validates the client_id parameter required for identifying
    which application's sessions to invalidate.
    """

    client_id = CharField(
        max_length=200,
        help_text="The OAuth2 application client ID.",
        error_messages={
            'required': 'client_id is required.',
            'blank': 'client_id cannot be blank.',
        }
    )


class ConvertTokenSerializer(Serializer):
    """Serializer for converting social provider tokens to OAuth2 tokens.

    Validates all parameters required for the token conversion flow.
    """

    grant_type = CharField(
        max_length=50,
        help_text="Must be 'convert_token'.",
        error_messages={
            'required': 'grant_type is required.',
            'blank': 'grant_type cannot be blank.',
        }
    )
    backend = CharField(
        max_length=200,
        help_text="Social auth backend name (e.g., 'facebook', 'google-oauth2').",
        error_messages={
            'required': 'backend is required.',
            'blank': 'backend cannot be blank.',
        }
    )
    client_id = CharField(
        max_length=200,
        help_text="The OAuth2 application client ID.",
        error_messages={
            'required': 'client_id is required.',
            'blank': 'client_id cannot be blank.',
        }
    )
    token = CharField(
        max_length=5000,
        help_text="Access token from the social provider.",
        error_messages={
            'required': 'token is required.',
            'blank': 'token cannot be blank.',
        }
    )


class RevokeTokenSerializer(Serializer):
    """Serializer for revoking OAuth2 tokens.

    Validates the client_id parameter required for token revocation.
    """

    client_id = CharField(
        max_length=200,
        help_text="The OAuth2 application client ID.",
        error_messages={
            'required': 'client_id is required.',
            'blank': 'client_id cannot be blank.',
        }
    )


class DisconnectBackendSerializer(Serializer):
    """Serializer for disconnecting a social auth backend.

    Validates parameters required to disconnect a social provider
    from a user's account.
    """

    backend = CharField(
        max_length=200,
        help_text="Social auth backend name to disconnect (e.g., 'facebook').",
        error_messages={
            'required': 'backend is required.',
            'blank': 'backend cannot be blank.',
        }
    )
    association_id = IntegerField(
        help_text="The ID of the social auth association to disconnect.",
        error_messages={
            'required': 'association_id is required.',
            'invalid': 'association_id must be a valid integer.',
        }
    )
