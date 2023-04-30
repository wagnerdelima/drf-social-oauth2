"""
drf-social-oauth2 is a frameworks meant to be used with Django and Django Rest Framework.
drf-social-oauth2 offers support to oauth2 authentication and authorization.
It's one of the easiest frameworks to integrate Oauth2 to your Django Rest Framework application.
By using drf-social-oauth2 you can authenticate with major vendors such as Google, Facebook, Instagram, Github, Twitter
and a ton more!
"""

__version__ = '2.1.2'

try:
    from secrets import SystemRandom
except ImportError:
    from random import SystemRandom


UNICODE_ASCII_CHARACTER_SET = (
    'abcdefghijklmnopqrstuvwxyz' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' '0123456789'
)


def generate_token(request, length=30, chars=UNICODE_ASCII_CHARACTER_SET):
    """Generates a non-guessable OAuth Json Web Token
    OAuth (1 and 2) does not specify the format of tokens except that they
    should be strings of random characters. Tokens should not be guessable
    and entropy when generating the random characters is important. Which is
    why SystemRandom is used instead of the default random.choice method.
    """
    from django.conf import settings
    from jose import jwt

    rand = SystemRandom()
    secret = getattr(settings, 'SECRET_KEY')

    token = ''.join(rand.choice(chars) for x in range(length))
    jwtted_token = jwt.encode({'token': token}, secret, algorithm='HS256')
    return jwtted_token
