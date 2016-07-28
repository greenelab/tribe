"""Common settings and globals."""

import datetime
from os.path import abspath, dirname, join, normpath
import os
from sys import path
from ConfigParser import SafeConfigParser

########## PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:
PROJECT_ROOT = dirname(dirname(abspath(__file__)))

# Site name:
SITE_NAME = 'tribe'

# Settings files
SETTINGS_ROOT = dirname(abspath(__file__))
SETTINGS_INI_FILES = normpath(join(SETTINGS_ROOT, 'settings'))

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(PROJECT_ROOT)
########## END PATH CONFIGURATION


########## CODESHIP CONFIG
cs = os.environ.get('CODESHIP_SETTINGS')
if cs == 'YES':
    pg_user = os.environ.get('PG_USER')
    pg_pass = os.environ.get('PG_PASSWORD')
    cs_secret = SafeConfigParser()
    cs_secret.read(normpath(join(SETTINGS_INI_FILES, 'example_secrets.ini')))
    import random
    cs_secret.set('secrets', 'SECRET_KEY', str(random.randint(0, 1000000)))
    cs_secret.set('database', 'DATABASE_PASSWORD', pg_pass)
    cs_secret.set('configfile', 'FILE_NAME', 'test.ini')
    cs_secret_fh = open(normpath(join(SETTINGS_INI_FILES, 'secrets.ini')), 'w')
    cs_secret.write(cs_secret_fh)
    cs_secret_fh.close()
    cs_config = SafeConfigParser()
    cs_config.read(normpath(join(SETTINGS_INI_FILES, 'test_template.ini')))
    cs_config.set('database', 'DATABASE_USER', pg_user)
    cs_config_fh = open(normpath(join(SETTINGS_INI_FILES, 'test.ini')), 'w')
    cs_config.write(cs_config_fh)
    cs_config_fh.close()
########## END CODESHIP CONFIG


########## INI CONFIGURATION
secrets = SafeConfigParser()
secrets.read(normpath(join(SETTINGS_INI_FILES, 'secrets.ini')))

config = SafeConfigParser()
# make sure to set the correct file name in the secrets.ini
config.read(normpath(join(SETTINGS_INI_FILES, secrets.get('configfile', 'FILE_NAME'))))
########## END INI CONFIGURATION


########## SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = secrets.get('secrets', 'SECRET_KEY')
########## END SECRET CONFIGURATION

########## DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = config.getboolean('debug', 'DEBUG')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
TEMPLATE_DEBUG = config.getboolean('debug', 'TEMPLATE_DEBUG')
########## END DEBUG CONFIGURATION


########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = tuple(config.items('error mail'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = tuple(config.items('404 mail'))
########## END MANAGER CONFIGURATION

########## SESSION COOKIE CONFIGURATION
SESSION_COOKIE_DOMAIN = config.get('cookies', 'SESSION_COOKIE_DOMAIN')
########## END SESSION COOKIE CONFIGURATION

########## TEST RUNNER CONFIG
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
########## END TEST RUNNER CONFIG


########## DATABASE CONFIGURATION
DATABASE_USER = config.get('database', 'DATABASE_USER')
DATABASE_PASSWORD = secrets.get('database', 'DATABASE_PASSWORD')
DATABASE_HOST = config.get('database', 'DATABASE_HOST')
DATABASE_PORT = config.get('database', 'DATABASE_PORT')
DATABASE_ENGINE = config.get('database', 'DATABASE_ENGINE')

# If the DB Engine is SQLite, this sets the file location to the proper place in the DB
if DATABASE_ENGINE == 'django.db.backends.sqlite3':
    DATABASE_NAME = normpath(join(PROJECT_ROOT, config.get('database', 'DATABASE_NAME')))
else:
    DATABASE_NAME = config.get('database', 'DATABASE_NAME')
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': DATABASE_ENGINE,
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,
    }
}
########## END DATABASE CONFIGURATION


########## GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'America/New_York'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
########## END GENERAL CONFIGURATION


########## MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = config.get('assets', 'MEDIA_ROOT')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = config.get('assets', 'MEDIA_URL')
########## END MEDIA CONFIGURATION


########## STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = config.get('assets', 'STATIC_URL')

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    normpath(join(PROJECT_ROOT, 'static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
########## END STATIC FILE CONFIGURATION


########## SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = tuple([x.strip() for x in config.get('debug', 'ALLOWED_HOSTS').split(',')])
########## END SITE CONFIGURATION


########## TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_DIRS = (
    normpath(join(PROJECT_ROOT, 'tribe/templates')),

    # This path has to be here to manually override allauth's templates
    # (we most likely want this for every Tribe instance)
    normpath(join(PROJECT_ROOT, 'profiles/templates')),
)
########## END TEMPLATE CONFIGURATION


########## MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes

DEFAULT_MIDDLEWARE_CLASSES = (
    'dogslow.WatchdogMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ADDON_MIDDLEWARE_CLASSES = (
    tuple([x.strip() for x in config.get('modules', 'ADDON_MIDDLEWARE').split(',')])
)
ADDON_MIDDLEWARE_CLASSES = filter(bool, ADDON_MIDDLEWARE_CLASSES) #filter empty (in case not configured)

MIDDLEWARE_CLASSES = DEFAULT_MIDDLEWARE_CLASSES + ADDON_MIDDLEWARE_CLASSES
########## END MIDDLEWARE CONFIGURATION


########## URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = '%s.urls' % SITE_NAME
########## END URL CONFIGURATION


########## WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME
########## END WSGI CONFIGURATION


########## APP CONFIGURATION
DJANGO_APPS = [
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

]

THIRD_PARTY_APPS = [x.strip() for x in config.get('modules', 'THIRD_PARTY').split(',')]
THIRD_PARTY_APPS = filter(bool, THIRD_PARTY_APPS) #filter empty (in case not configured)

# Apps specific for this project go here.
LOCAL_APPS = [
    'organisms',
    'genes',
    'genesets',
    'versions',
    'collaborations',
    'publications',
    'profiles',
]

########## END APP CONFIGURATION

# RAVEN CONFIGURATION
if secrets.has_section('raven'):
    print("Raven Enabled")
    LOCAL_APPS.append('raven.contrib.django.raven_compat')
    import raven
    RAVEN_CONFIG = {
        'dsn': secrets.get('raven', 'RAVEN_DSN'),
        # TODO: Figure out a way to do mercurial commit check
        # instead of git
        #'release': raven.fetch_git_sha(dirname(__file__)),
    }

# GOOGLE ANALYTICS
GOOGLE_ANALYTICS_KEY = secrets.get('ga', 'GOOGLE_ANALYTICS_KEY')

# HAYSTACK CONFIGURATION
if config.has_section('haystack'):
    LOCAL_APPS.append('haystack')
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': config.get('haystack', 'ENGINE'),
            'URL': config.get('haystack', 'URL'),
            'INDEX_NAME': config.get('haystack', 'INDEX_NAME'),
        }
    }
    HAYSTACK_ITERATOR_LOAD_PER_QUERY = int(config.get('haystack',
                                                      'LOAD_PER_QUERY'))
    HAYSTACK_SIGNAL_PROCESSOR = config.get('haystack',
                                           'HAYSTACK_SIGNAL_PROCESSOR')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
if config.has_section('sentry'):
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            },

        },
        'loggers': {
            'django': {
                'handlers': ['console', 'sentry',],
                'level': 'ERROR',
                'propagate': True,
            },

            'django.request': {
                'handlers': ['console', 'sentry','mail_admins',],
                'level': 'ERROR',
                'propagate': True,
            },
            '': {
                'handlers': ['console', 'sentry'],
                'level': config.get('log', 'LOG_LEVEL'),
                'propagate': True,
            },
            'raven': {
                'level': 'INFO',
                'handlers': ['console',],
                'propagate': False,
            },
            'sentry.errors': {
                'level': 'INFO',
                'handlers': ['console',],
                'propagate': False,
            },

        },
        'root': {
            'level': config.get('log', 'LOG_LEVEL'),
            'handlers': ['console', 'sentry'],
        },

    }

else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
            },
            '': {
                'handlers': ['console'],
                'level': config.get('log', 'LOG_LEVEL'),
                'propagate': True,
            },
        }
    }
########## END LOGGING CONFIGURATION


########## EMAIL CONFIGURATION

if config.has_section('email'):
    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
    EMAIL_HOST = config.get('email', 'EMAIL_HOST')

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
    EMAIL_HOST_PASSWORD = secrets.get('email', 'EMAIL_HOST_PASSWORD')

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
    EMAIL_HOST_USER = config.get('email', 'EMAIL_HOST_USER')

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
    EMAIL_PORT = config.get('email', 'EMAIL_PORT')

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
    EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
    EMAIL_USE_TLS = config.getboolean('email', 'EMAIL_USE_TLS')

    # See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
    SERVER_EMAIL = EMAIL_HOST_USER
else:
    # See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
########## END EMAIL CONFIGURATION


########## CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#    }
#}
########## END CACHE CONFIGURATION

########## ETOOLS CONFIGURATION
# allows us to query pubmed.
ETOOLS_CONFIG = {
    'base_url': 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
    'query_params': {
        'db': 'pubmed',
        'retmode': 'xml',
        'version': '2.0',
    }
}
########## END ETOOLS CONFIGURATION

########## TASTYPIE CONFIGURATION
# make angular and tastypie work together happily
# http://stackoverflow.com/questions/10555962/enable-django-and-tastypie-support-for-trailing-slashes
# and https://github.com/angular/angular.js/issues/992
TASTYPIE_ALLOW_MISSING_SLASH = True
APPEND_SLASH = False
########## END TASTYPIE CONFIGURATION

########## DOGSLOW CONFIGURATION
DOGSLOW = config.getboolean('dogslow', 'ENABLED')
DOGSLOW_LOGGER = 'dogslow'
DOGSLOW_LOG_TO_SENTRY = True
DOGSLOW_LOG_LEVEL = 'WARNING'
########## END DOGSLOW CONFIGURATION

########## OAUTH CONFIGURATION
if config.has_section('oauth'):
    OAUTH2_PROVIDER = {
        'ACCESS_TOKEN_EXPIRE_SECONDS': int(config.get(
            'oauth', 'ACCESS_TOKEN_EXPIRE_SECONDS'))
    }
    OAUTH_ACCESS_TOKEN_MODEL = config.get('oauth', 'OAUTH_ACCESS_TOKEN_MODEL')
########## END OAUTH CONFIGURATION

########## ALLAUTH CONFIGURATION
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend"
)

if config.has_section('allauth'):
    ACCOUNT_AUTHENTICATION_METHOD = config.get('allauth', 'ACCOUNT_AUTHENTICATION_METHOD')
    ACCOUNT_USERNAME_REQUIRED = config.getboolean('allauth', 'ACCOUNT_USERNAME_REQUIRED')
    ACCOUNT_EMAIL_REQUIRED = config.getboolean('allauth', 'ACCOUNT_EMAIL_REQUIRED')
    ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = int(config.get('allauth', 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS'))
    ACCOUNT_EMAIL_SUBJECT_PREFIX = config.get('allauth', 'ACCOUNT_EMAIL_SUBJECT_PREFIX')
    ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = config.get('allauth', 'ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL')
    ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = config.get('allauth', 'ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL')
########## END ALLAUTH CONFIGURATION

########## LOGIN REDIRECT
LOGIN_REDIRECT_URL = '/#/home'

########## DOCS CONFIGURATION
if config.has_section('documentation'):
    DOCS_URL = config.get('documentation', 'DOCS_URL')
########## END DOCS CONFIGURATION
