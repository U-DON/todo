from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.http import urlencode

import redis
from tastypie.test import ResourceTestCase

from .models import Task

@override_settings(
    CELERY_ALWAYS_EAGER = True,
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class TaskResourceTest(ResourceTestCase):
    def setUp(self):
        self.task_1 = Task.objects.create(title='Task 1')
        self.task_2 = Task.objects.create(title='Task 2')
        super(TaskResourceTest, self).setUp()

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def get_task_list_uri(self):
        return reverse('tasks:api_dispatch_list', kwargs={'resource_name': 'todo'})

    def get_task_uri(self, pk):
        return reverse('tasks:api_dispatch_detail', kwargs={'resource_name': 'todo', 'pk': pk})

    def test_resource_uris(self):
        self.assertEqual(self.get_task_list_uri(), '/todo')
        self.assertEqual(self.get_task_uri(self.task_1.pk), '/todo/{pk}'.format(pk=self.task_1.pk))

    def test_get_task_list(self):
        task_list_uri = self.get_task_list_uri()
        response = self.api_client.get(task_list_uri)
        self.assertValidJSONResponse(response)
        response = self.deserialize(response)
        self.assertEqual(len(response['objects']), 2)
        self.assertEqual(
            response['objects'][0],
            {
                'id': self.task_1.pk,
                'title': 'Task 1',
                'current': False,
                'done': False,
                'routine': False,
                'resource_uri': '/todo/{pk}'.format(pk=self.task_1.pk)
            }
        )
        self.assertEqual(
            response['objects'][1],
            {
                'id': self.task_2.pk,
                'title': 'Task 2',
                'current': False,
                'done': False,
                'routine': False,
                'resource_uri': '/todo/{pk}'.format(pk=self.task_2.pk)
            }
        )

    def test_get_task(self):
        task_uri = self.get_task_uri(self.task_1.pk)
        response = self.api_client.get(task_uri)
        self.assertValidJSONResponse(response)
        self.assertEqual(
            self.deserialize(response),
            {
                'id': self.task_1.pk,
                'title': 'Task 1',
                'current': False,
                'done': False,
                'routine': False,
                'resource_uri': task_uri
            }
        )

    def test_put_task(self):
        task_uri = self.get_task_uri(self.task_1.pk)
        old_data = self.deserialize(self.api_client.get(task_uri))
        new_data = old_data.copy()
        new_data['title'] = 'Task X'
        new_data['current'] = True
        new_data['done'] = True
        self.api_client.put(task_uri, data=new_data)
        task = Task.objects.get(pk=self.task_1.pk)
        self.assertEqual(task.title, 'Task X')
        self.assertTrue(task.is_current())
        self.assertTrue(task.is_done())

    def test_delete_task(self):
        self.assertEqual(Task.objects.count(), 2)
        task_uri = self.get_task_uri(self.task_1.pk)
        self.api_client.delete(task_uri)
        self.assertEqual(Task.objects.count(), 1)

@override_settings(
    CELERY_ALWAYS_EAGER = True,
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class TaskTest(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title='Task 1')

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def test_set_task_current(self):
        """Mark a task as current and check that it's current."""
        self.assertFalse(self.task.is_current())
        self.task.set_current(True)
        self.assertTrue(self.task.is_current())

    def test_set_task_done(self):
        """Mark a task as done and check that it's done."""
        self.assertFalse(self.task.is_done())
        self.task.set_done(True)
        self.assertTrue(self.task.is_done())

    def test_get_task_done_time(self):
        """Check that the done time of the task is the current time, both in UTC and accurate to the minute."""
        self.assertFalse(self.task.is_done())
        self.task.set_done(True)
        self.assertTrue(self.task.is_done())
        self.assertEqual(
            self.task.done_time().replace(second=0, microsecond=0),
            timezone.utc.localize(datetime.utcnow()).replace(second=0, microsecond=0)
        )
