from rest_framework.serializers import Serializer
from rest_framework.serializers import CharField


class InvalidateRefreshTokenSerializer(Serializer):
    """
    Validate the client_id required and length 100 characters for refresh tokens.
    """

    client_id = CharField(max_length=100)
