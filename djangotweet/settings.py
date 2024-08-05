"""
Django settings for djangotweet project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import environ
from celery.schedules import crontab

# BASE_DIR değişkenini tanımlayın
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise environment variables
env = environ.Env()
# Reading .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Load environment variables from .env file
load_dotenv()

# Azure Form Recognizer settings
AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING = "endpoint=https://arabulucu.europe.communication.azure.com/;accesskey=Yr6Dzdk+fuKj2pqAu3bjBbfOrjqH7+G37H8z2au4aCsfxOcvCGEYpkedoGV2yWSldEz+VTb64T0J3PQzlBN0WA=="

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ssqjin!cbl#@2=i$zf#g4epirt@yl^de_&fy#p09&5d28angu+"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['0888.nl', 'www.0888.nl', 'localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'face_result',
    'ocrapp',
    'access_tokens',
    'djmoney',
    'corsheaders',
    'widget_tweaks',
    "tweetapp.apps.TweetappConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat"
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "djangotweet.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = "djangotweet.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static_files'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/downloads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'downloads')



# CORS settings
CORS_ORIGIN_ALLOW_ALL = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = ""

# Oturum motoru ayarı (varsayılan olarak kullanılabilir)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

FACEBOOK_ACCESS_TOKEN = '8bbf68ef28c72e870923b8c85c633ff3'
FACEBOOK_AD_ACCOUNT_ID = '929453702313606'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'fetch_xml_data_every_5_minutes': {
        'task': 'face_result.tasks.fetch_xml_data',
        'schedule': crontab(minute='*/2'),  # Her 2 dakikada bir çalıştır
    },
    'fetch_facebook_posts_every_5_minutes': {
        'task': 'face_result.tasks.fetch_facebook_posts',
        'schedule': crontab(minute='*/10'),  # Her 10 dakikada bir çalıştır
    },
}
