from django.conf import settings

import redis

def active_task_ids():
    r = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    r.set_response_callback('SMEMBERS', (lambda s: set([int(e) for e in s])))
    return r.smembers('active')

def done_task_ids():
    r = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    r.set_response_callback('SMEMBERS', (lambda s: set([int(e) for e in s])))
    return r.smembers('done')
