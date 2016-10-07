import os
import json


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'admin_honeypot',
    'bootstrap3',
    'el_pagination',
    'compressor',
    'accounts',
    'bot',
    'home',
    'pages',
    'serve_media',
    'events',
    'gallery',
    'groups',
    'django_rq',
    'surveys',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'templates/error_pages')],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'static/locale/'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')

# Redirect to here after Login
LOGIN_REDIRECT_URL = '/home'

# Media root directory
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    'pipeline.finders.PipelineFinder',
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

PIPELINE = {
    'PIPELINE_ENABLED': True,
    'COMPILERS': (
        'pipeline.compilers.stylus.StylusCompiler',
    ),
    'STYLESHEETS': {
        'main': {
            'source_filenames': (
                'style/main.styl',
            ),
            'output_filename': 'style/main.css',
        }
    },
    'STYLUS_ARGUMENTS': '-c',
}

CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")

############################################################################
# Insert Path to secrets file in SECRET_PATH
#
# The File should look like this
#
# {
#   "TELEGRAM_TOKEN": "",
#   "DB_PASSWORD": "",
#   "TELEGRAM_WEBHOOK_SECRET": "",
#   "SECRET_KEY":""
# }
#############################################################################

SECRET_PATH = '/var/secrets/secrets.json'

secrets_file = open(SECRET_PATH).read()
secrets = json.loads(secrets_file)

TELEGRAM_WEBHOOK_SECRET = secrets["TELEGRAM_WEBHOOK_SECRET"]
TELEGRAM_TOKEN = secrets["TELEGRAM_TOKEN"]
SECRET_KEY = secrets["SECRET_KEY"]

##############################################################################
# Insert Telegrambot username in TELEGRAM_BOT_USERNAME
TELEGRAM_BOT_USERNAME = "botusername"

DEBUG = False

##############################################################################
# Insert your allowed domains/ips in ALLOWED_HOSTS
ALLOWED_HOSTS = ['localhost']

COMPRESS_ENABLED = True

# a global static file directory
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

##############################################################################
# Insert your database information here
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'database',
        'USER': 'groupsome',
        'PASSWORD': secrets["DB_PASSWORD"],
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '/var/run/redis/redis.sock',
    },
}

RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
    }
}

MEDIA_SERVE_USING_NGINX = True

ADMIN_HONEYPOT_EMAIL_ADMINS = False

SECURE_CONTENT_TYPE_NOSNIFF = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
