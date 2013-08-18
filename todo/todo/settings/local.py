import redis

from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'todo',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
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
