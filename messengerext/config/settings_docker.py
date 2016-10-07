from .settings_base import *
import os
import random
import sys

for var in ["TELEGRAM_BOT_USERNAME", "TELEGRAM_TOKEN", "MYSQL_PASSWORD"]:
    if var not in os.environ:
        sys.exit("missing environment variable %s" % var)

if os.path.isfile("/django-secret.txt"):
    with open("/django-secret.txt") as f:
        SECRET_KEY = f.read().strip()
else:
    SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
                          for i in range(50)])
    with open("/django-secret.txt", "w") as f:
        f.write(SECRET_KEY)

ALLOWED_HOSTS = ["*"]
MEDIA_ROOT = '/uploaded-media/'
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")
TELEGRAM_WEBHOOK_SECRET = ""
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

DEBUG = False

COMPRESS_ENABLED = True

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'groupsome',
        'USER': 'groupsome',
        'PASSWORD': os.getenv("MYSQL_PASSWORD"),
        'HOST': 'db',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'redis:6379',
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
