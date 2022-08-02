"""
Django settings for ga_core project.
"""
import os

from pathlib import Path
from django.contrib.messages import constants
from dotenv import load_dotenv

# Passwords and database credentials stored in .env file
# NOT IN VERSION CONTROL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

try:
    # env variables will either be set to environment when run (loaded in
    # manage.py), or when run via docker and passed with --env-file
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = os.environ.get('GENETIC_DEBUG', False)

    # DNANexus Token
    DNANEXUS_TOKEN = os.environ['DNANEXUS_TOKEN']

    PROD_HOST = os.environ['PROD_HOST']
    DEBUG_HOST = os.environ['DEBUG_HOST']
    CSRF_TRUSTED_ORIGINS = os.environ['CSRF_TRUSTED_ORIGINS']

    # hosts in config read as str, convert to list
    PROD_HOST = [host.strip() for host in PROD_HOST.split(',')]
    DEBUG_HOST = [host.strip() for host in DEBUG_HOST.split(',')]
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in CSRF_TRUSTED_ORIGINS.split(',')]

    # Database (not used currently)
    # ACCOUNT_DB_NAME = os.environ['ACCOUNT_DB_NAME']
    # ACCOUNT_DB_USER = os.environ['ACCOUNT_DB_USER']
    # ACCOUNT_DB_PASSWORD = os.environ['ACCOUNT_DB_PASSWORD']
    # ACCOUNT_DB_HOST = os.environ['ACCOUNT_DB_HOST']

    # GOOGLE_ANALYTICS = os.environ['GOOGLE_ANALYTICS']

    # SMTP Email
    EMAIL_USER = os.environ['EMAIL_USER']
    SMTP_RELAY = os.environ['SMTP_RELAY']
    PORT = os.environ['PORT']
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']

    # IGVs
    FASTA_37 = os.environ['FASTA_37']
    FASTA_IDX_37 = os.environ['FASTA_IDX_37']
    CYTOBAND_37 = os.environ['CYTOBAND_37']
    REFSEQ_37 = os.environ['REFSEQ_37']

    FASTA_38 = os.environ['FASTA_38']
    FASTA_IDX_38 = os.environ['FASTA_IDX_38']
    CYTOBAND_38 = os.environ['CYTOBAND_38']
    REFSEQ_38 = os.environ['REFSEQ_38']

    GENOMES = os.environ['GENOMES']

    PROJECT_CNVS = os.environ['PROJECT_CNVS']
    DEV_PROJECT_NAME = os.environ['DEV_PROJECT_NAME']

    # Primer IGV Download URL
    PRIMER_DOWNLOAD = os.environ['PRIMER_DOWNLOAD']

    # Slack Token
    SLACK_TOKEN = os.environ['SLACK_TOKEN']


except KeyError as e:
    key = e.args[0]
    raise KeyError(
        f'Unable to import {key} from environment, is an .env file '
        'present or env variables set?'
    )


if DEBUG:
    print(f"Running in debug mode, accessible hosts: {DEBUG_HOST}")
    ALLOWED_HOSTS = DEBUG_HOST
else:
    print(f"Running in production mode, accessible hosts: {PROD_HOST}")
    ALLOWED_HOSTS = PROD_HOST


INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',  # required for serving static files
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
    # pip installed app
    'django_tables2',
    'crispy_forms',
    'corsheaders'
]

# django crispy forms for nice form rendering
CRISPY_TEMPLATE_PACK = 'bootstrap4'


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
    constants.DEBUG: 'alert-secondary',
    constants.INFO: 'alert-info',
    constants.SUCCESS: 'alert-success',
    constants.WARNING: 'alert-warning',
    constants.ERROR: 'alert-danger',
}

WSGI_APPLICATION = 'ga_core.wsgi.application'


# Database (not used currently)
# default engine (django.db.backends.mysql)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': ACCOUNT_DB_NAME,
#         'USER': ACCOUNT_DB_USER,
#         'PASSWORD': ACCOUNT_DB_PASSWORD,
#         'HOST': ACCOUNT_DB_HOST,
#         'PORT': 3306
#     }
# }


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
TIME_ZONE = 'Europe/London'
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
with open('/home/ga/logs/ga-error.log', 'a+'):
    pass
with open('/home/ga/logs/ga-debug.log', 'a+'):
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{'
        }
    },
    # Handlers
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/ga/logs/ga-debug.log',
            'formatter': 'standard',
            'maxBytes': 1024*1024*5,
            'backupCount': 2
        },
        'error_log': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/ga/logs/ga-error.log',
            'formatter': 'standard',
            'maxBytes': 1024*1024*5,
            'backupCount': 2
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'general': {
            'handlers': ['error_log'],
            'level': 'DEBUG',
            'propagate': True
        }
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
# Explanation on why:
# https://www.mattlayman.com/understand-django/serving-static-files/
STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:1337',
    'dl.ec1.dnanex.us'
]
# CORS_ALLOW_ALL_ORIGINS = True
