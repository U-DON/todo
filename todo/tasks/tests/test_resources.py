from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from mock import patch
import redis
from tastypie.test import ResourceTestCase

from ..models import Task, History

@override_settings(
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
        """Returns the URI for all tasks."""
        return reverse('tasks:api_dispatch_list', kwargs={'resource_name': 'todo'})

    def get_task_uri(self, pk):
        """Returns the URI for a specific task."""
        return reverse('tasks:api_dispatch_detail', kwargs={'resource_name': 'todo', 'pk': pk})

    def test_resource_uris(self):
        """Checks that the generated URIs are correct."""
        self.assertEqual(self.get_task_list_uri(), '/todo')
        self.assertEqual(self.get_task_uri(self.task_1.pk), '/todo/{pk}'.format(pk=self.task_1.pk))

    def test_get_task_list(self):
        """Makes a GET request for all tasks and checks that the response contains all."""
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
        """Makes a GET request for a single task and checks that the response is correct."""
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

    @patch('tasks.models.schedule_archival')
    def test_put_task(self, mock_schedule_archival):
        """Make a PUT request for a single task and checks that the task data is updated."""
        task_uri = self.get_task_uri(self.task_1.pk)
        old_data = self.deserialize(self.api_client.get(task_uri))
        new_data = old_data.copy()
        new_data['title'] = 'Task X'
        new_data['current'] = True
        new_data['done'] = True
        self.api_client.put(task_uri, data=new_data)
        mock_schedule_archival.assert_called_once()
        task = Task.objects.get(pk=self.task_1.pk)
        self.assertEqual(task.title, 'Task X')
        self.assertTrue(task.is_current())
        self.assertTrue(task.is_done())

    def test_delete_task(self):
        """Makes a DELETE request for a single task and checks that it's deleted."""
        self.assertEqual(Task.objects.count(), 2)
        task_uri = self.get_task_uri(self.task_1.pk)
        self.api_client.delete(task_uri)
        self.assertEqual(Task.objects.count(), 1)
