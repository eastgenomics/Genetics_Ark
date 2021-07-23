"""
Django settings for ga_core project.
"""
from dotenv import load_dotenv, find_dotenv
import logging.config
import os
from pathlib import Path
import sys

from django.contrib.messages import constants as messages
from pathlib import Path


# Passwords and database credentials stored in config.py
# NOT IN VERSION CONTROL
# from .config import SECRET_KEY, PROD_HOST, DEBUG_HOST, GOOGLE_ANALYTICS,\
#     EMAIL_USER, EMAIL_PASSWORD, SEND_GRID_API_KEY, EMAIL_ADDRESS

env_variables = [
    'SECRET_KEY', 'PROD_HOST', 'DEBUG_HOST', 'PROD_DATABASE', 'DEBUG_DATABASE',
    'GOOGLE_ANALYTICS', 'EMAIL_USER', 'SMTP_RELAY', 'PORT'

]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# either load config from local .env or try get from env variables
try:
    env_file = os.path.join(os.path.dirname(__file__), '../genetics_ark.env')

    if Path(env_file).is_file():
        # import from env file if present, else assume already set
        load_dotenv(env_file)

    SECRET_KEY = os.environ['SECRET_KEY']
    PROD_HOST = os.environ['PROD_HOST']
    DEBUG_HOST = os.environ['DEBUG_HOST']
    PROD_DATABASE = os.environ['PROD_DATABASE']
    DEBUG_DATABASE = os.environ['DEBUG_DATABASE']
    AUTH_TOKEN = os.environ['AUTH_TOKEN']
    GOOGLE_ANALYTICS = os.environ['GOOGLE_ANALYTICS']
    EMAIL_USER = os.environ['EMAIL_USER']
    SMTP_RELAY = os.environ['SMTP_RELAY']
    PORT = os.environ['PORT']

    # URLs for IGV
    FASTA_37 = os.environ['FASTA_37']
    FASTA_IDX_37 = os.environ['FASTA_IDX_37']
    CYTOBAND_37 = os.environ['CYTOBAND_37']
    REFSEQ_37 = os.environ['REFSEQ_37']

    FASTA_38 = os.environ['FASTA_38']
    FASTA_IDX_38 = os.environ['FASTA_IDX_38']
    CYTOBAND_38 = os.environ['CYTOBAND_38']
    REFSEQ_38 = os.environ['REFSEQ_38']

    # path to bulk design script in primer designer
    PRIMER_DESIGNER_PATH = os.environ['PRIMER_DESIGNER_PATH']

except KeyError:
    raise KeyError(
        'Unable to import required key from environment, is an .env file '
        'present or env variables set?'
    )


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# DEBUG= False

if DEBUG:
    ALLOWED_HOSTS = '*'
else:
    ALLOWED_HOSTS = PROD_HOST


INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    # own apps
    'genetics_ark',
    'accounts',
    'DNAnexus_to_igv',
    'primer_designer',
    # default django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'crispy_forms'
]

# django crispy forms for nice form rendering
CRISPY_TEMPLATE_PACK = 'bootstrap4'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'ga_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

WSGI_APPLICATION = 'ga_core.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ark_accounts',
        'USER': 'root',
        'PASSWORD': '9fdnmhrT!!',
        # 'HOST': 'jethro-T490'
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                'MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'NumericPasswordValidator'),
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Settings for account app email verification
EMAIL_HOST = SMTP_RELAY
EMAIL_PORT = PORT
EMAIL_HOST_USER = EMAIL_USER
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_USER  # email address for sending activation emails

# whitenoise static file serving compression & cacheing
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


# Settings for logging
log_dir = os.path.join(BASE_DIR, "logs")
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamp': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    # Handlers
    'handlers': {
        'debug-file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{log_dir}/ga-debug.log',
            'formatter': 'timestamp'
        },
        'error-file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': f'{log_dir}/ga-error.log',
            'formatter': 'timestamp'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'timestamp'
        },
    },
    # Loggers
    'loggers': {
        'ga_debug': {
            'handlers': ['debug-file'],
            'level': 'DEBUG',
            'propagate': True,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG')
        },
        'ga_error': {
            'handlers': ['error-file'],
            'level': 'ERROR',
            'propagate': True,
            'level': "ERROR"
        },
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = '/static/'

# STATIC_ROOT = os.path.join(BASE_DIR, 'root')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

LOGIN_REDIRECT_URL = 'home'
