from rest_framework.serializers import Serializer
from rest_framework.serializers import CharField, IntegerField


class InvalidateRefreshTokenSerializer(Serializer):
    """
    Validate the client_id required and length 100 characters for refresh tokens.
    """

    client_id = CharField(max_length=200)


class InvalidateSessionsSerializer(Serializer):
    client_id = CharField(max_length=200)


class ConvertTokenSerializer(Serializer):
    grant_type = CharField(max_length=50)
    backend = CharField(max_length=200)
    client_id = CharField(max_length=200)
    token = CharField(max_length=5000)


class RevokeTokenSerializer(Serializer):
    client_id = CharField(max_length=200)


class DisconnectBackendSerializer(Serializer):
    backend = CharField(max_length=200)
    association_id = IntegerField()
