"""
Django settings for statsapp project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os

import environ
from pathlib import Path


live_deploy = False

env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

if live_deploy:
    DEBUG = False

    ALLOWED_HOSTS = env('ALLOWED_HOSTS_LIVE').split(' ')

    # Database
    # https://docs.djangoproject.com/en/4.1/ref/settings/#databases
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env('DB_NAME_LIVE'),
            'USER': env('DB_USER_LIVE'),
            'PASSWORD': env('DB_PASSWORD_LIVE'),
            'HOST': env('DB_HOST_LIVE'),
            'PORT': '',
        }
    }

else:
    DEBUG = True

    ALLOWED_HOSTS = []

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME_DEV'),
            'USER': env('DB_USER_DEV'),
            'PASSWORD': env('DB_PASSWORD_DEV'),
            'HOST': env('DB_HOST_DEV'),
            'PORT': env('DB_PORT_DEV'),
        }
    }

# Application definition

INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_pdb',
    'django_celery_beat',
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'ajax_datatable',
    "debug_toolbar",
      # Мои
    'applications.accounts.apps.AccountsConfig',
    'applications.netcost.apps.NetcostConfig',
    'applications.autoconverter.apps.AutoconverterConfig',
    'applications.calls.apps.CallsConfig',
    'applications.auction.apps.AuctionConfig',
    'applications.srav.apps.SravConfig',
    'applications.ads.apps.AdsConfig',
    'libs.services.apps.ServicesConfig',
    'libs.autoru.apps.AutoruConfig',
    'libs.teleph.apps.TelephConfig',

]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MIDDLEWARE_CLASSES = (
    'django_pdb.middleware.PdbMiddleware',
)

ROOT_URLCONF = 'stats.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            BASE_DIR / 'libs/services/templatetags',
        ],
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

WSGI_APPLICATION = 'stats.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'accounts.Client'
LOGIN_REDIRECT_URL = '/accounts/profile/'

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

if live_deploy:
    STATIC_ROOT = '/home/django/django_venv/src/staticfiles/'


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Celery settings
if live_deploy:
    # CELERY_BROKER_URL = env('CELERY_BROKER_URL_LIVE')
    # CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND_LIVE')

    CELERY_BROKER_URL = env('CELERY_BROKER_URL_DEV')
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND_DEV')

elif not live_deploy:
    CELERY_BROKER_URL = env('CELERY_BROKER_URL_DEV')
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND_DEV')

CELERY_SEND_TASK_ERROR_EMAILS = True

# CELERY_BEAT_SCHEDULE = {
#     'scheduled_task': {
#         'task': 'statsapp.tasks.test_task',
#         'schedule': 5.0,
#     }
# }

ALLOW_UNICODE_SLUGS = True

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

DATA_UPLOAD_MAX_MEMORY_SIZE = 15_242_880

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': f'{BASE_DIR}/logs/django_logs.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['file']
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = os.environ['EMAIL_PORT']
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['EMAIL_LOGIN']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_PASSWORD']

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'stats_cache'),
    }
}

INTERNAL_IPS = (
    "127.0.0.1",
    "212.57.103.141",
)

WEBSITE = env('WEBSITE')

# Принудительно показывает Django Debug Toolbar без ограничений по ip
# def show_toolbar(request):
#     return True
#
#
# DEBUG_TOOLBAR_CONFIG = {
#     "SHOW_TOOLBAR_CALLBACK": show_toolbar,
# }

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}
