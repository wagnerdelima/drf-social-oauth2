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
        'NAME': 'database',
        'HOST': 'db',
        'PORT': 5432,
        'USER': 'user',
        'PASSWORD': 'password',
    }
}


TEST_LOCAL_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('HOST'),
        'PORT': int(os.getenv('PORT', 666)),
        'NAME': os.getenv(
            'POSTGRES_DB',
        ),
        'USER': os.getenv(
            'POSTGRES_USER',
        ),
        'PASSWORD': os.getenv(
            'POSTGRES_PASSWORD',
        ),
    }
}


DRFSO2_PROPRIETARY_BACKEND_NAME = 'Django'
DRFSO2_URL_NAMESPACE = 'drf'

ROOT_URLCONF = 'drf_social_oauth2.urls'

USE_TZ = True
