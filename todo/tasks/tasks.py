from django.conf import settings

import celery
import redis

@celery.task
def archive_task(task_id):
    redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    redis_pipeline = redis_client.pipeline()
    redis_pipeline.srem('todo:current', task_id) \
                  .srem('todo:done', task_id) \
                  .delete('todo#{task_id}'.format(task_id=task_id)) \
                  .execute()
