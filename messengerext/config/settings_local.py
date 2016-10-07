from .settings_base import *

SECRET_KEY = '()fvp=cm+=quyxz*_3v+gjg!d)8n0(wbo*k)(0kwtwuryr4nil'
DEBUG = True


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# a global static file directory
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# cache location (memory for debug)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    }
}
