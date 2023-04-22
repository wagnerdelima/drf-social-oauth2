from rest_framework.serializers import Serializer
from rest_framework.serializers import CharField, IntegerField


class InvalidateRefreshTokenSerializer(Serializer):
    """
    Validate the client_id required and length 100 characters for refresh tokens.
    """

    client_id = CharField(max_length=100)


class InvalidateSessionsSerializer(Serializer):
    client_id = CharField(max_length=100)


class ConvertTokenSerializer(Serializer):
    grant_type = CharField(max_length=32)
    backend = CharField(max_length=100)
    client_id = CharField(max_length=100)
    client_secret = CharField(max_length=255)
    token = CharField(max_length=500)


class RevokeTokenSerializer(Serializer):
    client_id = CharField(max_length=100)
    client_secret = CharField(max_length=255)
    token = CharField(max_length=500)


class DisconnectBackendSerializer(Serializer):
    backend = CharField(max_length=50)
    association_id = IntegerField()
