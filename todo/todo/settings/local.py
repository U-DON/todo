import redis

from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'todo',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}

REDIS_CONF = {
    'HOST': 'localhost',
    'PORT': 6379,
    'DB': 0
}

REDIS_POOL = redis.ConnectionPool(
    host=REDIS_CONF['HOST'],
    port=REDIS_CONF['PORT'],
    db=REDIS_CONF['DB']
)

BROKER_URL = "redis://{host}:{port}/{db}".format(
    host=REDIS_CONF['HOST'],
    port=REDIS_CONF['PORT'],
    db=REDIS_CONF['DB']
)

CELERY_RESULT_BACKEND = BROKER_URL
