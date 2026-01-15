"""
drf-social-oauth2 is a framework meant to be used with Django and Django Rest Framework.

drf-social-oauth2 offers support to OAuth2 authentication and authorization.
It's one of the easiest frameworks to integrate OAuth2 to your Django Rest Framework application.
By using drf-social-oauth2 you can authenticate with major vendors such as Google, Facebook,
Instagram, Github, Twitter and a ton more!
"""

from secrets import SystemRandom
from typing import Any

__version__ = '3.1.0'

__all__ = [
    '__version__',
    'generate_token',
    'UNICODE_ASCII_CHARACTER_SET',
]

UNICODE_ASCII_CHARACTER_SET: str = (
    'abcdefghijklmnopqrstuvwxyz' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' '0123456789'
)


def generate_token(
    request: Any,
    length: int = 30,
    chars: str = UNICODE_ASCII_CHARACTER_SET
) -> str:
    """Generate a non-guessable OAuth JSON Web Token.

    OAuth (1 and 2) does not specify the format of tokens except that they
    should be strings of random characters. Tokens should not be guessable
    and entropy when generating the random characters is important. Which is
    why SystemRandom is used instead of the default random.choice method.

    Args:
        request: The HTTP request object (unused but required by oauth2_provider).
        length: The length of the random token string. Defaults to 30.
        chars: The character set to use for token generation.

    Returns:
        A JWT-encoded token string.
    """
    from django.conf import settings
    import jwt

    rand = SystemRandom()
    secret: str = getattr(settings, 'SECRET_KEY')

    token = ''.join(rand.choice(chars) for _ in range(length))
    jwtted_token: str = jwt.encode({'token': token}, secret, algorithm='HS256')
    return jwtted_token
