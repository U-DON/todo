import calendar
from datetime import date
import dateutil.parser
import pytz

from django.conf import settings
from django.db import models
from django.utils import timezone

import redis

class TaskManager(models.Manager):
    def get_query_set(self):
        return super(TaskManager, self).get_query_set()

    def current_task_ids(self):
        """Return set of task ids for tasks that are in progress."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.smembers('todo:current')

    def done_task_ids(self):
        """Return set of task ids for tasks that have been done today."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.smembers('todo:done')

    def current(self):
        """Return all tasks in progress."""
        current_tasks = self.current_task_ids()
        return self.filter(pk__in=current_tasks)

    def later(self):
        """Return all tasks queued for later."""
        current_tasks = self.current_task_ids()
        return self.exclude(pk__in=current_tasks)

    def done(self):
        """Return all tasks that are done."""
        done_tasks = self.done_task_ids()
        return self.filter(pk__in=done_tasks)

class Task(models.Model):
    description = models.TextField()
    routine = models.BooleanField(default=False)
    title = models.CharField(max_length=200)

    objects = TaskManager()

    def is_current(self):
        """Return True if the task is in progress."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.sismember('todo:current', self.pk)

    def is_done(self):
        """Return True if the task has been completed today if it's a routine or if it has been completed ever if it only ever happens once."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.sismember('todo:done', self.pk)

    def done_time(self):
        """Return the time (in UTC) the task was completed."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        done_time = redis_client.hget('todo#{task_id}'.format(task_id=self.pk), 'done_time')
        return dateutil.parser.parse(done_time) if done_time is not None else None

    def epoch_done_time(self):
        """Return the done time (in milliseconds) relative to the epoch."""
        done_time = self.done_time()
        return int(calendar.timegm(done_time.timetuple())) * 1000 if done_time is not None else None

    def __unicode__(self):
        return self.title
