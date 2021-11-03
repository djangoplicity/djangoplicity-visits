"""
Django settings for test project.

Generated by 'django-admin startproject' using Django 1.11.21.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# We can't use ugettext from django.utils.translation as it will itself
# load the settings resulting in a ImproperlyConfigured error
ugettext = lambda s: s

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(BASE_DIR, 'tmp')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')o0n4t(00@de#j2h77p%3u#t$vfpg266nwdb42kw%q9ca283!0'

SHORT_NAME = 'visits'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
DJANGOPLICITY_APPS = [
    'djangoplicity',
    'djangoplicity.menus',
    'djangoplicity.reports',
    'djangoplicity.pages',
    'djangoplicity.media',
    'djangoplicity.archives',
    'djangoplicity.archives.contrib.security',
    'djangoplicity.announcements',
    'djangoplicity.science',
    'djangoplicity.releases',
    'djangoplicity.metadata',
    'djangoplicity.adminhistory',
    'djangoplicity.utils',
    'djangoplicity.celery',
    'djangoplicity.iframe',
    'djangoplicity.admincomments',
    'djangoplicity.simplearchives',
    'djangoplicity.actions',
    'djangoplicity.cutter',
    'djangoplicity.visits',
]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.redirects',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'test_project',
    'tinymce'
]

INSTALLED_APPS = DJANGO_APPS + DJANGOPLICITY_APPS + THIRD_PARTY_APPS


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'test_project.urls'

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

WSGI_APPLICATION = 'test_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'djangoplicity-visits',
        'USER': 'djangoplicity-visits',
        'PASSWORD': 'djangoplicity-visits',
        'HOST': 'djangoplicity-visits-db',
        'PORT': '5432',
    }
}

if os.environ.get('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'djangoplicity-visits',
            'USER': 'djangoplicity-visits',
            'PASSWORD': 'djangoplicity-visits',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGES = (
    ('en', ugettext('English')),
)

LANGUAGE_CODE = 'en'

SITE_ID = 1

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

# JAVASCRIPT CUSTOM CONFIG
JQUERY_JS = "jquery/jquery-1.11.1.min.js"
JQUERY_UI_JS = "jquery-ui-1.12.1/jquery-ui.min.js"
JQUERY_UI_CSS = "jquery-ui-1.12.1/jquery-ui.min.css"
DJANGOPLICITY_ADMIN_CSS = "djangoplicity/css/admin.css"
DJANGOPLICITY_ADMIN_JS = "djangoplicity/js/admin.js"
SUBJECT_CATEGORY_CSS = "djangoplicity/css/widgets.css"

IMAGES_ARCHIVE_ROOT = 'archives/images/'
VIDEOS_ARCHIVE_ROOT = 'archives/videos/'
SCIENCEANNOUNCEMENTS_ARCHIVE_ROOT = 'archives/science/'
RELEASE_ARCHIVE_ROOT = 'archives/releases/'
