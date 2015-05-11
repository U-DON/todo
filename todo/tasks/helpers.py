from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

import pytz
import redis

# from .tasks import archive_tasks

def schedule_archival(user_id):
    """Schedules a job to archive done tasks at midnight in the given user's local time."""
    user_key = 'user#{user_id}'.format(user_id=user_id)
    redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
    if not redis_client.hexists(user_key, 'archive_task_id') and redis_client.exists('todo:done'):
        utc_datetime = timezone.utc.localize(datetime.utcnow())
        local_timezone = pytz.timezone('America/New_York')
        local_datetime = utc_datetime.astimezone(local_timezone)
        local_midnight = local_timezone.localize(datetime.combine(local_datetime.date() + timedelta(days=1), time()))
        midnight = local_midnight.astimezone(timezone.utc)
        celery_result = archive_tasks.apply_async(args=[user_id], eta=midnight)
        redis_client.hset(user_key, 'archive_task_id', celery_result.id)
