from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.http import urlencode

import redis

from .models import Task

@override_settings(
    CELERY_ALWAYS_EAGER = True,
    REDIS_POOL = redis.ConnectionPool(
        host='localhost',
        port=6380,
        db=0
    )
)
class TaskTest(TestCase):
    def setUp(self):
        Task.objects.create(title="Task 1", is_routine=False)

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def test_set_task_current(self):
        """Mark a task as current and check that it's current."""
        task = Task.objects.get(title="Task 1")
        self.assertFalse(task.is_current())
        task.set_current(True)
        self.assertTrue(task.is_current())

    def test_set_task_done(self):
        """Mark a task as done and check that it's done."""
        task = Task.objects.get(title="Task 1")
        self.assertFalse(task.is_done())
        task.set_done(True)
        self.assertTrue(task.is_done())

    def test_get_task_done_time(self):
        """Check that the done time of the task is the current time, both in UTC and accurate to the minute."""
        task = Task.objects.get(title="Task 1")
        self.assertFalse(task.is_done())
        task.set_done(True)
        self.assertTrue(task.is_done())
        self.assertEqual(
            task.done_time().replace(second=0, microsecond=0),
            timezone.utc.localize(datetime.utcnow()).replace(second=0, microsecond=0)
        )
