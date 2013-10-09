from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.http import urlencode

from mock import patch
import redis
from tastypie.test import ResourceTestCase

from .models import Task, History
from .tasks import archive_tasks

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
        """Return the URI for all tasks."""
        return reverse('tasks:api_dispatch_list', kwargs={'resource_name': 'todo'})

    def get_task_uri(self, pk):
        """Return the URI for a specific task."""
        return reverse('tasks:api_dispatch_detail', kwargs={'resource_name': 'todo', 'pk': pk})

    def test_resource_uris(self):
        """Check that the generated URIs are correct."""
        self.assertEqual(self.get_task_list_uri(), '/todo')
        self.assertEqual(self.get_task_uri(self.task_1.pk), '/todo/{pk}'.format(pk=self.task_1.pk))

    def test_get_task_list(self):
        """Make a GET request for all tasks and check that the response contains all."""
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
        """Make a GET request for a single task and check that the response is correct."""
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
        """Make a PUT request for a single task and check that the task data is updated."""
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
        """Make a DELETE request for a single task and check that it's deleted."""
        self.assertEqual(Task.objects.count(), 2)
        task_uri = self.get_task_uri(self.task_1.pk)
        self.api_client.delete(task_uri)
        self.assertEqual(Task.objects.count(), 1)

@override_settings(
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class TaskTest(TestCase):
    def setUp(self):
        self.task_1 = Task.objects.create(title='Task 1')
        self.task_2 = Task.objects.create(title='Task 2', is_routine=True)

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def test_set_task_current(self):
        """Mark a task as current and check that it's current."""
        self.assertFalse(self.task_1.is_current())
        self.task_1.set_current(True)
        self.assertTrue(self.task_1.is_current())

    def test_set_current_task_not_current(self):
        """Mark a current task as not current and check that it's not current."""
        self.task_1.set_current(True)
        self.assertTrue(self.task_1.is_current())
        self.task_1.set_current(False)
        self.assertFalse(self.task_1.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_task_done(self, mock_schedule_archival):
        """Mark a task as done and check that it's done and current."""
        self.assertFalse(self.task_1.is_done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        self.assertTrue(self.task_1.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_done_task_not_done(self, mock_schedule_archival):
        """Mark a done task as not done and check that it's not done and still current."""
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        self.assertTrue(self.task_1.is_current())
        self.task_1.set_done(False)
        self.assertFalse(self.task_1.is_done())
        self.assertTrue(self.task_1.is_current())

    @patch('tasks.models.schedule_archival')
    def test_get_task_done_time(self, mock_schedule_archival):
        """Check that the done time of the task is the current time, both in UTC and accurate to the minute."""
        self.assertFalse(self.task_1.is_done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        self.assertEqual(
            self.task_1.done_time().replace(second=0, microsecond=0),
            timezone.utc.localize(datetime.utcnow()).replace(second=0, microsecond=0)
        )

    @patch('tasks.models.schedule_archival')
    def test_task_current_before_and_not_after_archival(self, mock_schedule_archival):
        """Check that a done task is current before archival and not after."""
        self.assertFalse(self.task_1.is_current())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_current())
        archive_tasks.apply()
        self.assertFalse(self.task_1.is_current())

    @patch('tasks.models.schedule_archival')
    def test_reminder_done_before_and_after_archival(self, mock_schedule_archival):
        """Check that a done reminder is done before and after archival."""
        self.assertFalse(self.task_1.is_done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        archive_tasks.apply()
        self.assertTrue(self.task_1.is_done())

    @patch('tasks.models.schedule_archival')
    def test_routine_done_before_and_not_after_archival(self, mock_schedule_archival):
        """Check that a done routine is done before archival and not after."""
        self.assertFalse(self.task_2.is_done())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2.is_done())
        archive_tasks.apply()
        self.assertFalse(self.task_2.is_done())

@override_settings(
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class HistoryTest(TestCase):
    def setUp(self):
        self.task_1 = Task.objects.create(title='Task 1')

    @patch('tasks.models.schedule_archival')
    def test_history_exists_after_task_archival(self, mock_schedule_archival):
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_1.history.count(), 1)

    @patch('tasks.models.schedule_archival')
    def test_task_done_time_is_history_done_time(self, mock_schedule_archival):
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_1.done_time(), self.task_1.history.all()[0].done_time)

@override_settings(
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class TaskManagerTest(TestCase):
    def setUp(self):
        self.task_1 = Task.objects.create(title='Task 1')
        self.task_2 = Task.objects.create(title='Task 2', is_routine=True)

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def test_current_reminder_in_current_query_set(self):
        """Mark a reminder as current and check that it's in the query set of current but not later tasks."""
        self.assertFalse(self.task_1 in Task.objects.current())
        self.assertTrue(self.task_1 in Task.objects.later())
        self.task_1.set_current(True)
        self.assertTrue(self.task_1 in Task.objects.current())
        self.assertFalse(self.task_1 in Task.objects.later())

    def test_current_routine_in_current_query_set(self):
        """Mark a routine as current and check that it's in the query set of current but not later tasks."""
        self.assertFalse(self.task_2 in Task.objects.current())
        self.assertTrue(self.task_2 in Task.objects.later())
        self.task_2.set_current(True)
        self.assertTrue(self.task_2 in Task.objects.current())
        self.assertFalse(self.task_2 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_in_done_query_set(self, mock_schedule_archival):
        """Mark a reminder done and check that it's in the query sets of done and current but not later tasks."""
        self.assertFalse(self.task_1 in Task.objects.done())
        self.assertTrue(self.task_1 in Task.objects.later())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1 in Task.objects.done())
        self.assertFalse(self.task_1 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_in_done_query_set(self, mock_schedule_archival):
        """Mark a routine done and check that it's in the query sets of done and current but not later tasks."""
        self.assertFalse(self.task_2 in Task.objects.done())
        self.assertTrue(self.task_2 in Task.objects.later())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2 in Task.objects.done())
        # Note that archival has not happened as this point, so task should still be current.
        self.assertFalse(self.task_2 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_and_routine_in_done_query_set(self, mock_schedule_archival):
        """Mark a reminder and a routine done and check that both are in the query set of done tasks."""
        self.assertFalse(self.task_1 in Task.objects.done())
        self.assertFalse(self.task_2 in Task.objects.done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1 in Task.objects.done())
        self.assertFalse(self.task_1 in Task.objects.later())
        self.assertTrue(self.task_2 in Task.objects.done())
        self.assertFalse(self.task_2 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_in_done_query_set_before_and_after_archival(self, mock_schedule_archival):
        """Check that a done reminder is in the query set of done tasks before and after archival."""
        self.assertFalse(self.task_1 in Task.objects.done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1 in Task.objects.done())
        archive_tasks.apply()
        self.assertTrue(self.task_1 in Task.objects.done())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_not_in_done_query_set_after_archival(self, mock_schedule_archival):
        """Check that a done routine is in the query set of done tasks before archival and not after."""
        self.assertFalse(self.task_2 in Task.objects.done())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2 in Task.objects.done())
        archive_tasks.apply()
        self.assertFalse(self.task_2 in Task.objects.done())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_not_in_later_query_set_before_or_after_archival(self, mock_schedule_archival):
        """Check that a done reminder is not in the query set of later tasks before or after archival."""
        self.assertTrue(self.task_1 in Task.objects.later())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertFalse(self.task_1 in Task.objects.later())
        archive_tasks.apply()
        self.assertFalse(self.task_1 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_in_later_query_set_after_archival(self, mock_schedule_archival):
        """Check that a done routine is in the query set of later tasks after archival and not before."""
        self.assertTrue(self.task_2 in Task.objects.later())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertFalse(self.task_2 in Task.objects.later())
        archive_tasks.apply()
        self.assertTrue(self.task_2 in Task.objects.later())
