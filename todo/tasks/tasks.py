from django.conf import settings

from celery import Celery
import redis

celery = Celery('tasks')

@celery.task
def clean_tasks():
    redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    redis_pipeline = redis_client.pipeline()
    while True:
        try:
            redis_pipeline.watch('todo:done')
            task_ids = redis_pipeline.smembers('todo:done')
            redis_pipeline.multi()
            for task_id in task_ids:
                redis_pipeline.srem('todo:active', task_id) \
                              .srem('todo:done', task_id) \
                              .delete('todo#{task_id}'.format(task_id=task_id))
            redis_pipeline.execute()
            break
        except WatchError:
            continue
