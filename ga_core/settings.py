"""
Django settings for ga_core project.
"""
import os

from pathlib import Path
from django.contrib.messages import constants

# Passwords and database credentials stored in .env file
# NOT IN VERSION CONTROL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


try:
    # env variables will either be set to environment when run (loaded in
    # manage.py), or when run via docker and passed with --env-file
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = os.environ['DEBUG']  # should be false in production
    AUTH_TOKEN = os.environ['AUTH_TOKEN']

    PROD_HOST = os.environ['PROD_HOST']
    DEBUG_HOST = os.environ['DEBUG_HOST']

    # hosts in config read as str, convert to list
    PROD_HOST = PROD_HOST.replace(' ', '').split(',')
    DEBUG_HOST = DEBUG_HOST.replace(' ', '').split(',')

    ACCOUNT_DB_NAME = os.environ['ACCOUNT_DB_NAME']
    ACCOUNT_DB_USER = os.environ['ACCOUNT_DB_USER']
    ACCOUNT_DB_PASSWORD = os.environ['ACCOUNT_DB_PASSWORD']
    ACCOUNT_DB_HOST = os.environ['ACCOUNT_DB_HOST']

    GOOGLE_ANALYTICS = os.environ['GOOGLE_ANALYTICS']

    REF_37 = os.environ['REF_37']
    REF_38 = os.environ['REF_38']
    DBSNP_37 = os.environ['DBSNP_37']
    DBSNP_38 = os.environ['DBSNP_38']

    EMAIL_USER = os.environ['EMAIL_USER']
    SMTP_RELAY = os.environ['SMTP_RELAY']
    PORT = os.environ['PORT']
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']

    # URLs for IGV
    FASTA_37 = os.environ['FASTA_37']
    FASTA_IDX_37 = os.environ['FASTA_IDX_37']
    CYTOBAND_37 = os.environ['CYTOBAND_37']
    REFSEQ_37 = os.environ['REFSEQ_37']

    FASTA_38 = os.environ['FASTA_38']
    FASTA_IDX_38 = os.environ['FASTA_IDX_38']
    CYTOBAND_38 = os.environ['CYTOBAND_38']
    REFSEQ_38 = os.environ['REFSEQ_38']

    # path to primer designer & its reference files
    PRIMER_DESIGNER_DIR_PATH = os.environ['PRIMER_DESIGNER_DIR_PATH']
    PRIMER_DESIGNER_REF_PATH = os.environ['PRIMER_DESIGNER_REF_PATH']

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
    'django_tables2',
    'crispy_forms',
    # 'django_q'
]

# django crispy forms for nice form rendering
CRISPY_TEMPLATE_PACK = 'bootstrap4'


MIDDLEWARE = [
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


# Database
# default engine (django.db.backends.mysql) doesn't work with dockerized django app
# mysql engine: mysql.connector.django
# https://stackoverflow.com/questions/54633968/2059-authentication-plugin-caching-sha2-password-when-running-server-conne/54649081#54649081
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': ACCOUNT_DB_NAME,
        'USER': ACCOUNT_DB_USER,
        'PASSWORD': ACCOUNT_DB_PASSWORD,
        'HOST': ACCOUNT_DB_HOST,
        'PORT': 3306
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
# Explanation on why: https://www.mattlayman.com/understand-django/serving-static-files/
STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

LOGIN_REDIRECT_URL = 'home'

Q_CLUSTER = {
    'name': 'DjangORM',
    'timeout': 300,
    'retry': 350,
    'orm': 'default'
}
