import os

import dj_database_url
import redis

from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

REDIS_CONF = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

REDIS_POOL = redis.ConnectionPool(**REDIS_CONF)

BROKER_URL = "redis://{host}:{port}/{db}".format(**REDIS_CONF)

CELERY_RESULT_BACKEND = BROKER_URL

BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 86400
}

# Parse database configuration from $DATABASE_URL
DATABASES['default'] =  dj_database_url.config()

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static asset configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
