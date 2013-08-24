from datetime import date

from django.db import models

from .helpers import active_task_ids, done_task_ids

class TaskManager(models.Manager):
    def get_query_set(self):
        return super(TaskManager, self).get_query_set()

    def active(self):
        active_tasks = active_task_ids()
        return self.filter(pk__in=active_tasks)

    def inactive(self):
        active_tasks = active_task_ids()
        return self.exclude(pk__in=active_tasks)

    def done(self):
        done_tasks = self._done_ids()
        return self.filter(pk__in=done_tasks)

class Task(models.Model):
    description = models.TextField()
    # routine = models.BooleanField(default=False)
    title = models.CharField(max_length=200)

    objects = TaskManager()

    def active(self):
        return self.pk in active_task_ids()

    def done(self):
        # if self.routine:
        return self.pk in done_task_ids()
        # return self.activities.count() > 0 

    def __unicode__(self):
        return self.title

# Keep track of when tasks start and end to know whether to mark it for today or later
# Validate that there are only eight tasks that are not done and start today or before
#   class Activity(models.Model):
#       task = models.ForeignKeyField(Task, related_name='activities')
#       done_date = models.DateField(null=True)
