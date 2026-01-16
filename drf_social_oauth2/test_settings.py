import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'secret_key'

DEBUG = True

ALLOWED_HOSTS = [
    'testserver',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
    'social_django',
    'drf_social_oauth2',
    'rest_framework',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'database'),
        'HOST': os.getenv('HOST', 'db'),
        'PORT': int(os.getenv('PORT', 5432)),
        'USER': os.getenv('POSTGRES_USER', 'user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'password'),
    }
}


DRFSO2_PROPRIETARY_BACKEND_NAME = 'Django'
DRFSO2_URL_NAMESPACE = 'drf'

ROOT_URLCONF = 'drf_social_oauth2.urls'

USE_TZ = True

# OAuth2 Provider settings with refresh token rotation enabled
OAUTH2_PROVIDER = {
    # Refresh token rotation: issue new refresh token on each use
    'ROTATE_REFRESH_TOKEN': True,
    # Reuse protection: revoke all tokens if a used refresh token is reused
    'REFRESH_TOKEN_REUSE_PROTECTION': True,
    # Grace period: seconds the old refresh token remains valid after rotation
    'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 0,
    # Refresh token lifetime in seconds (14 days)
    'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,
    # Access token lifetime in seconds (1 hour)
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
}
