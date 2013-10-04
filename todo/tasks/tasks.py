from django.conf import settings

import celery
import redis
from redis.exceptions import WatchError

@celery.task
def archive_tasks():
    """Clear done tasks from Redis and archive information in main database.

    If a new task is marked done during archiving, restart the job so \
    it gets cleaned up as well.
    
    Without cleaning up tasks marked done during this job, there are \
    no guarantees that it will be cleaned up next midnight, particularly \
    if no subsequent tasks are marked done later that day.

    """
    redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    redis_pipeline = redis_client.pipeline()
    while True:
        try:
            redis_pipeline.watch('todo:done')
            task_ids = redis_pipeline.smembers('todo:done')
            redis_pipeline.multi()
            for task_id in task_ids:
                redis_pipeline.srem('todo:current', task_id) \
                              .srem('todo:done', task_id) \
                              .delete('todo#{task_id}'.format(task_id=task_id))
            # Remove the stored archival task id so a new archival can be scheduled later.
            redis_pipeline.delete('archive_task_id') \
                          .execute()
            break
        except WatchError:
            continue
        finally:
            redis_pipeline.reset()
