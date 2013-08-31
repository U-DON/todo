from datetime import date

from django.db import models

from .helpers import active_task_ids, done_task_ids

class TaskManager(models.Manager):
    def get_query_set(self):
        return super(TaskManager, self).get_query_set()

    def active(self):
        """Return all tasks in progress."""
        active_tasks = active_task_ids()
        return self.filter(pk__in=active_tasks)

    def inactive(self):
        """Return all tasks queued for later."""
        active_tasks = active_task_ids()
        return self.exclude(pk__in=active_tasks)

    def done(self):
        """Return all tasks that are done."""
        done_tasks = self.done_task_ids()
        return self.filter(pk__in=done_tasks)
        # return self.filter(Q(pk__in=done_tasks) | Q(routine=False, activity__done_date__lte=date.today()))

class Task(models.Model):
    description = models.TextField()
    routine = models.BooleanField(default=False)
    title = models.CharField(max_length=200)

    objects = TaskManager()

    def active(self):
        """Return True if the task is in progress."""
        return self.pk in active_task_ids()

    def done(self):
        """Return True if the task has been completed today if it's a routine or if it has been completed ever if it only ever happens once."""
        # if self.routine:
        return self.pk in done_task_ids()
        # return self.activities.count() > 0 

    def __unicode__(self):
        return self.title
