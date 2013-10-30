import calendar
from datetime import datetime
import dateutil.parser

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

import redis

from .helpers import schedule_archival

class TaskManager(models.Manager):
    def get_query_set(self):
        return super(TaskManager, self).get_query_set()

    def current_task_ids(self):
        """Returns set of task ids for tasks that are in progress."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.smembers('todo:current')

    def done_task_ids(self):
        """Returns set of task ids for tasks that have been done today."""
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.smembers('todo:done')

    def current(self):
        """Returns all tasks in progress."""
        current_tasks = self.current_task_ids()
        return self.filter(pk__in=current_tasks)

    def later(self):
        """Returns all tasks queued for later."""
        current_tasks = self.current_task_ids()
        return self.exclude(pk__in=current_tasks).exclude(
            is_routine=False,
            history__isnull=False
        )

    def done(self):
        """Returns all tasks that are done.

        Tasks that are done are either tasks in the set of current done tasks \
        or reminders that have a history entry.

        """
        done_tasks = self.done_task_ids()
        return self.filter(
            models.Q(pk__in=done_tasks) |
            models.Q(
                is_routine=False,
                history__isnull=False
            )
        )

class Task(models.Model):
    description = models.TextField()
    is_routine = models.BooleanField(default=False)
    title = models.CharField(max_length=200)
    user = models.ForeignKey(get_user_model(), related_name='tasks')

    objects = TaskManager()

    def is_archived(self):
        """Returns True if the task has at least one history entry."""
        return self.history.count() > 0

    def is_current(self):
        """Returns True if the task is in progress.

        A task is in progress if it exists in the set of current tasks.

        """
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        return redis_client.sismember('todo:current', self.pk)

    def is_done(self):
        """Returns True if the task is done.

        A routine is done if it has been completed today (exists in the set \
        of current done tasks).

        A reminder is done if it has been completed ever (exists in the set \
        of current done tasks or has a history entry).

        """
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        is_done_today = redis_client.sismember('todo:done', self.pk)
        if self.is_routine:
            return is_done_today 
        else:
            return is_done_today or self.is_archived()

    def set_current(self, current):
        """Marks a task as current or not current.

        If current, add the task to the set of current tasks. \
        Remove if not current.

        If the task is a reminder that has been archived, do nothing.

        """
        if not self.is_routine and self.is_archived():
            return
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        if current:
            redis_client.sadd('todo:current', self.pk)
        else:
            redis_client.srem('todo:current', self.pk)

    def set_done(self, done):
        """Marks a task as done or not done.

        If done, add the task to the set of current done tasks and \
        schedule the task for archival. If the task is a reminder \
        that has been archived, do nothing.

        If not done, remove the task from the set of current done tasks. \
        If the task is a reminder that has been archived, remove its history.

        """
        if not self.is_routine and self.is_archived():
            if not done:
                self.history.all()[0].delete()
            return
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        redis_pipeline = redis_client.pipeline()
        if done:
            if not self.is_current():
                self.set_current(done)
            now = timezone.utc.localize(datetime.utcnow())
            redis_pipeline.sadd('todo:done', self.pk) \
                          .hset('todo#{task_id}'.format(task_id=self.pk), 'done_time', now) \
                          .execute()
            schedule_archival()
        else:
            redis_pipeline.srem('todo:done', self.pk) \
                          .delete('todo#{task_id}'.format(task_id=self.pk)) \
                          .execute()

    def done_time(self):
        """Returns the time (in UTC) the task was completed.

        For routines, return the most recent done time.

        """
        if self.is_archived():
            history = self.history.order_by('-done_time')
            return history[0].done_time
        redis_client = redis.StrictRedis(connection_pool=settings.REDIS_POOL)
        done_time = redis_client.hget('todo#{task_id}'.format(task_id=self.pk), 'done_time')
        return dateutil.parser.parse(done_time) if done_time is not None else None

    def epoch_done_time(self):
        """Returns the done time (in milliseconds) relative to the epoch."""
        done_time = self.done_time()
        return int(calendar.timegm(done_time.timetuple())) * 1000 if done_time is not None else None

    def __iter__(self):
        for field in self._meta.get_all_field_names():
            yield (field, getattr(self, field))

    def __unicode__(self):
        return self.title

class History(models.Model):
    task = models.ForeignKey(Task, related_name='history')
    done_time = models.DateTimeField()

    def __unicode__(self):
        return "{task_title} - {done_time}".format(
            task_title=self.task.title,
            done_time=self.done_time
        )
