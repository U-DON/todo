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
            task_history = {}
            redis_pipeline.watch('todo:done')
            task_ids = redis_pipeline.smembers('todo:done')
            # First iteration over task ids sets watches and aggregates task info.
            for task_id in task_ids:
                # Collect the done times for each task in a dictionary.
                task_key = 'todo#{task_id}'.format(task_id=task_id)
                redis_pipeline.watch(task_key)
                done_time = redis_pipeline.hget(task_key, 'done_time')
                task_history[task_id] = done_time
            redis_pipeline.multi()
            # Second iteration builds the transaction to clean up temporary task info.
            for task_id in task_ids:
                task_key = 'todo#{task_id}'.format(task_id=task_id)
                redis_pipeline.srem('todo:current', task_id) \
                              .srem('todo:done', task_id) \
                              .delete(task_key)
            # Remove the stored archival task id so a new archival can be scheduled later.
            redis_pipeline.delete('archive_task_id') \
                          .execute()
            break
        except WatchError:
            continue
        finally:
            redis_pipeline.reset()
    # Create history entries for each task after the Redis cleanup.
    # Import Task here since importing at the top of the module raises ImportError.
    from .models import Task
    for task_id, done_time in task_history.iteritems():
        task = Task.objects.get(pk=task_id)
        task.history.create(done_time=done_time)
