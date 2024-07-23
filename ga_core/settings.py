"""
Django settings for ga_core project.
"""
import os

from pathlib import Path
from django.contrib.messages import constants
from dotenv import load_dotenv

import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

try:
    # env variables will either be set to environment when run (loaded in
    # manage.py), or when run via docker and passed with --env-file
    SECRET_KEY = os.environ["SECRET_KEY"]
    DEBUG = os.environ.get("GENETIC_DEBUG", False)
    LOCAL_WORKSTATION = os.environ.get("LOCAL_WORKSTATION", False)

    # DNANexus Token
    DNANEXUS_TOKEN = os.environ["DNANEXUS_TOKEN"]

    PROD_HOST = os.environ["PROD_HOST"]
    DEBUG_HOST = os.environ["DEBUG_HOST"]
    CSRF_TRUSTED_ORIGINS = os.environ["CSRF_TRUSTED_ORIGINS"]

    # hosts in config read as str, convert to list
    PROD_HOST = [host.strip() for host in PROD_HOST.split(",")]
    DEBUG_HOST = [host.strip() for host in DEBUG_HOST.split(",")]
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in CSRF_TRUSTED_ORIGINS.split(",")
    ]

    # IGVs
    FASTA_37 = os.environ["FASTA_37"]
    FASTA_IDX_37 = os.environ["FASTA_IDX_37"]
    CYTOBAND_37 = os.environ["CYTOBAND_37"]
    REFSEQ_37 = os.environ["REFSEQ_37"]
    REFSEQ_INDEX_37 = os.environ["REFSEQ_INDEX_37"]

    FASTA_38 = os.environ["FASTA_38"]
    FASTA_IDX_38 = os.environ["FASTA_IDX_38"]
    CYTOBAND_38 = os.environ["CYTOBAND_38"]
    REFSEQ_38 = os.environ["REFSEQ_38"]
    REFSEQ_INDEX_38 = os.environ["REFSEQ_INDEX_38"]

    GENOMES = os.environ["GENOMES"]

    PROJECT_CNVS = os.environ["PROJECT_CNVS"]
    DEV_PROJECT_NAME = os.environ["DEV_PROJECT_NAME"]

    # Primer IGV Download URL
    PRIMER_DOWNLOAD = os.environ["PRIMER_DOWNLOAD"]

    # Slack Token
    SLACK_TOKEN = os.environ["SLACK_TOKEN"]

    # Grid Links
    GRID_SERVICE_DESK = os.environ["GRID_SERVICE_DESK"]

    AUTH_LDAP_BIND_DN = os.environ["BIND_DN"]
    AUTH_LDAP_BIND_PASSWORD = os.environ["BIND_PASSWORD"]

    DB_NAME = os.environ["DB_NAME"]
    DB_USERNAME = os.environ["DB_USERNAME"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_PORT = os.environ["DB_PORT"]
    DB_HOST = os.environ["DB_HOST"]

    AUTH_LDAP_SERVER_URI = os.environ["AUTH_LDAP_SERVER_URI"]
    LDAP_CONF = os.environ["LDAP_CONF"]
    LDAP_PERMITTED_GROUP = os.environ["LDAP_PERMITTED_GROUP"]

except KeyError as e:
    key = e.args[0]
    raise KeyError(
        f"Unable to import {key} from environment, is an .env file "
        "present or env variables set?"
    )


if DEBUG:
    print(f"Running in debug mode, accessible hosts: {DEBUG_HOST}")
    ALLOWED_HOSTS = DEBUG_HOST
else:
    print(f"Running in production mode, accessible hosts: {PROD_HOST}")
    ALLOWED_HOSTS = PROD_HOST


INSTALLED_APPS = [
    # own apps
    "genetics_ark",
    "accounts",
    "DNAnexus_to_igv",
    "primer_designer",
    # default django
    "django.contrib.admin",  # admin
    "django.contrib.auth",  # core of authentication framework
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # pip installed app
    "crispy_forms",
    "corsheaders",
    "crispy_bootstrap5",
    "user_visit",
    "django_q",
]

# Django crispy forms bootstrap configuration
CRISPY_TEMPLATE_PACK = "bootstrap5"


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "user_visit.middleware.UserVisitMiddleware",  # user visit Middleware
]

ROOT_URLCONF = "ga_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Error/Info message class configuration
MESSAGE_TAGS = {
    constants.DEBUG: "alert-secondary",
    constants.INFO: "alert-info",
    constants.SUCCESS: "alert-success",
    constants.WARNING: "alert-warning",
    constants.ERROR: "alert-danger",
}

WSGI_APPLICATION = "ga_core.wsgi.application"

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DB_NAME,
        "USER": DB_USERNAME,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "NumericPasswordValidator"),
    },
]

# Login url
LOGIN_URL = (
    "/genetics_ark/accounts/login" if not LOCAL_WORKSTATION else "/accounts/login"
)

# Define where to redirect users after login
LOGIN_REDIRECT_URL = "/genetics_ark/igv" if not LOCAL_WORKSTATION else "/igv"

# Authentication Configuration
# this also checks that the logged-in user is Authorised, e.g., that they
# are a member of the LDAP group specified in the config file
AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0}

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    LDAP_CONF, ldap.SCOPE_SUBTREE, "(samaccountname=%(user)s)"
)

LDAPSearch("dc=net,dc=addenbrookes,dc=nhs,dc=uk", ldap.SCOPE_SUBTREE, "(uid=%(user)s)")

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    LDAP_PERMITTED_GROUP,
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfNames)',
)

AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr='cn')

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
}

AUTH_LDAP_REQUIRE_GROUP = LDAP_PERMITTED_GROUP

AUTH_LDAP_FIND_GROUP_PERMS = True

AUTH_LDAP_CACHE_TIMEOUT = 3600

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Settings for logging
LOG_DIR = "/home/ga/logs/" if not LOCAL_WORKSTATION else "logs/"
ERROR_LOGDIR = LOG_DIR + "ga-error.log"
DEBUG_LOGDIR = LOG_DIR + "ga-debug.log"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{levelname} {asctime} {name} {message}", "style": "{"}
    },
    # Handlers
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "error_log": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOGDIR,
            "formatter": "standard",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 2,
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "general": {"handlers": ["error_log"], "level": "DEBUG", "propagate": True},
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
# Explanation on why:
# https://www.mattlayman.com/understand-django/serving-static-files/
STATIC_URL = "genetics_ark/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

CORS_ALLOWED_ORIGINS = ["http://localhost:80", "https://dl.ec1.dnanex.us"]

# Redis for async task queue
Q_CLUSTER = {
    "timeout": None,
    "max_attempts": 1,
    "workers": 1,  # 2 or more will cause memory alloc issue
    "redis": {
        "host": "redis",
        "port": 6379,
        "db": 0,
        "password": None,
        "socket_timeout": None,
        "charset": "utf-8",
        "errors": "strict",
        "unix_socket_path": None,
    },
}

LOGOUT_REDIRECT_URL = "/genetics_ark" if not LOCAL_WORKSTATION else "/"
