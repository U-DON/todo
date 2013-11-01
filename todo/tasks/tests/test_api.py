from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
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
        self.client = Client()
        self.username = 'test@test.com'
        self.password = 'test'
        self.user = get_user_model().objects.create_user(email=self.username, name='test', password=self.password)
        self.reminder = self.user.tasks.create(title='Reminder')
        self.routine = self.user.tasks.create(title='Routine', is_routine=True)
        super(TaskResourceTest, self).setUp()

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def get_credentials(self):
        return self.api_client.client.login(username=self.username, password=self.password)

    def get_task_list_uri(self):
        """Returns the URI for all tasks."""
        return reverse('api_dispatch_list', kwargs={'api_name': 'api', 'resource_name': 'todo'})

    def get_task_uri(self, pk):
        """Returns the URI for a specific task."""
        return reverse('api_dispatch_detail', kwargs={'api_name': 'api', 'resource_name': 'todo', 'pk': pk})

    def test_resource_uris(self):
        """Checks that the generated URIs are correct."""
        self.assertEqual(self.get_task_list_uri(), '/api/todo')
        self.assertEqual(self.get_task_uri(self.reminder.pk), '/api/todo/{pk}'.format(pk=self.reminder.pk))

    def test_get_task_list_unauthorized(self):
        """Makes a GET request for a list of tasks without the proper credentials and checks that it's invalid."""
        task_list_uri = self.get_task_list_uri()
        self.assertHttpUnauthorized(self.api_client.get(task_list_uri))

    def test_get_task_list(self):
        """Makes a GET request for a list of tasks and checks that the response contains all the user's tasks."""
        task_list_uri = self.get_task_list_uri()
        response = self.api_client.get(task_list_uri, authentication=self.get_credentials())
        self.assertValidJSONResponse(response)
        response = self.deserialize(response)
        self.assertEqual(len(response['objects']), 2)
        self.assertEqual(
            response['objects'][1],
            {
                'id': self.reminder.pk,
                'title': 'Reminder',
                'current': False,
                'done': False,
                'routine': False,
                'resource_uri': '/api/todo/{pk}'.format(pk=self.reminder.pk),
                'user': self.user.email
            }
        )
        self.assertEqual(
            response['objects'][0],
            {
                'id': self.routine.pk,
                'title': 'Routine',
                'current': False,
                'done': False,
                'routine': True,
                'resource_uri': '/api/todo/{pk}'.format(pk=self.routine.pk),
                'user': self.user.email
            }
        )

    def test_get_task_unauthorized(self):
        """Makes a GET request for a single task without the proper credentials and checks that it's invalid."""
        task_uri = self.get_task_uri(self.reminder.pk)
        self.assertHttpUnauthorized(self.api_client.get(task_uri))

    def test_get_task(self):
        """Makes a GET request for a single task and checks that the response is correct."""
        task_uri = self.get_task_uri(self.reminder.pk)
        response = self.api_client.get(task_uri, authentication=self.get_credentials())
        self.assertValidJSONResponse(response)
        self.assertEqual(
            self.deserialize(response),
            {
                'id': self.reminder.pk,
                'title': 'Reminder',
                'current': False,
                'done': False,
                'routine': False,
                'resource_uri': task_uri,
                'user': self.user.email
            }
        )

    def test_put_task_unauthorized(self):
        """Makes a PUT request for a single task without the proper credentials and checks that it's invalid."""
        task_uri = self.get_task_uri(self.reminder.pk)
        old_data = self.deserialize(self.api_client.get(task_uri, authentication=self.get_credentials()))
        self.api_client.client.logout()
        new_data = old_data.copy()
        new_data['title'] = 'Task X'
        new_data['current'] = True
        new_data['done'] = True
        self.assertHttpUnauthorized(self.api_client.put(task_uri, data=new_data))
        task = Task.objects.get(pk=self.reminder.pk)
        self.assertFalse(task.is_current())
        self.assertFalse(task.is_done())

    @patch('tasks.models.schedule_archival')
    def test_put_task(self, mock_schedule_archival):
        """Make a PUT request for a single task and checks that the task data is updated."""
        task_uri = self.get_task_uri(self.reminder.pk)
        old_data = self.deserialize(self.api_client.get(task_uri, authentication=self.get_credentials()))
        new_data = old_data.copy()
        new_data['title'] = 'Task X'
        new_data['current'] = True
        new_data['done'] = True
        self.api_client.put(task_uri, data=new_data, authentication=self.get_credentials())
        mock_schedule_archival.assert_called_once()
        task = Task.objects.get(pk=self.reminder.pk)
        self.assertEqual(task.title, 'Task X')
        self.assertTrue(task.is_current())
        self.assertTrue(task.is_done())

    def test_delete_task_unauthorized(self):
        """Makes a DELETE request for a single task without the proper credentials and checks that it's invalid."""
        self.assertEqual(Task.objects.count(), 2)
        task_uri = self.get_task_uri(self.reminder.pk)
        self.assertHttpUnauthorized(self.api_client.delete(task_uri))
        self.assertEqual(Task.objects.count(), 2)

    def test_delete_task(self):
        """Makes a DELETE request for a single task and checks that it's deleted."""
        self.assertEqual(Task.objects.count(), 2)
        task_uri = self.get_task_uri(self.reminder.pk)
        self.api_client.delete(task_uri, authentication=self.get_credentials())
        self.assertEqual(Task.objects.count(), 1)
