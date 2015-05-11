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
        'HOST': '',
        'PORT': '',
    }
}

LOGGING['loggers']['django'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': True
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

REDIS_CONF = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

TEST_REDIS_CONF = REDIS_CONF.copy()
TEST_REDIS_CONF['port'] = 6380

REDIS_POOL = redis.ConnectionPool(**REDIS_CONF)

BROKER_URL = "redis://{host}:{port}/{db}".format(**REDIS_CONF)

BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 86400
}
