import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'secret_key'

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
]

DRFSO2_PROPRIETARY_BACKEND_NAME = 'Django'

DRFSO2_URL_NAMESPACE = 'drf'

ROOT_URLCONF = 'drf_social_oauth2.urls'
