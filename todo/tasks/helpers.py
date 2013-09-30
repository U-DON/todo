from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

import celery
import pytz
import redis
from redis.exceptions import WatchError

from .tasks import archive_tasks

def schedule_archival():
    redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    utc_datetime = timezone.utc.localize(datetime.utcnow())
    local_timezone = pytz.timezone('America/New_York')
    local_datetime = utc_datetime.astimezone(local_timezone)
    local_midnight = local_timezone.localize(datetime.combine(local_datetime.date() + timedelta(days=1), time()))
    midnight = local_midnight.astimezone(timezone.utc)
    if not redis_client.exists('archive_task_id'):
        celery_result = archive_tasks.apply_async(eta=midnight)
        redis_client.set('archive_task_id', celery_result.id)

def unschedule_archival():
    redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    if not redis_client.exists('todo:done') and redis_client.exists('archive_task_id'):
        archive_task_id = redis_client.get('archive_task_id')
        celery.current_app.control.revoke(archive_task_id, terminate=True)
        redis_client.delete('archive_task_id')
