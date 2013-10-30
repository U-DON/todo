from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from mock import patch
import redis

from ..models import Task, History
from ..tasks import archive_tasks

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
        """Marks a reminder as current and checks that it's in the query set of current but not later tasks."""
        self.assertFalse(self.task_1 in Task.objects.current())
        self.assertTrue(self.task_1 in Task.objects.later())
        self.task_1.set_current(True)
        self.assertTrue(self.task_1 in Task.objects.current())
        self.assertFalse(self.task_1 in Task.objects.later())

    def test_current_routine_in_current_query_set(self):
        """Marks a routine as current and checks that it's in the query set of current but not later tasks."""
        self.assertFalse(self.task_2 in Task.objects.current())
        self.assertTrue(self.task_2 in Task.objects.later())
        self.task_2.set_current(True)
        self.assertTrue(self.task_2 in Task.objects.current())
        self.assertFalse(self.task_2 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_in_done_query_set(self, mock_schedule_archival):
        """Marks a reminder done and checks that it's in the query sets of done and current but not later tasks."""
        self.assertFalse(self.task_1 in Task.objects.done())
        self.assertTrue(self.task_1 in Task.objects.later())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1 in Task.objects.done())
        self.assertFalse(self.task_1 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_in_done_query_set(self, mock_schedule_archival):
        """Marks a routine done and checks that it's in the query sets of done and current but not later tasks."""
        self.assertFalse(self.task_2 in Task.objects.done())
        self.assertTrue(self.task_2 in Task.objects.later())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2 in Task.objects.done())
        # Note that archival has not happened as this point, so task should still be current.
        self.assertFalse(self.task_2 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_and_routine_in_done_query_set(self, mock_schedule_archival):
        """Marks a reminder and a routine done and checks that both are in the query set of done tasks."""
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
        """Checks that a done reminder is in the query set of done tasks before and after archival."""
        self.assertFalse(self.task_1 in Task.objects.done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1 in Task.objects.done())
        archive_tasks.apply()
        self.assertTrue(self.task_1 in Task.objects.done())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_not_in_done_query_set_after_archival(self, mock_schedule_archival):
        """Checks that a done routine is in the query set of done tasks before archival and not after."""
        self.assertFalse(self.task_2 in Task.objects.done())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2 in Task.objects.done())
        archive_tasks.apply()
        self.assertFalse(self.task_2 in Task.objects.done())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_not_in_later_query_set_before_or_after_archival(self, mock_schedule_archival):
        """Checks that a done reminder is not in the query set of later tasks before or after archival."""
        self.assertTrue(self.task_1 in Task.objects.later())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertFalse(self.task_1 in Task.objects.later())
        archive_tasks.apply()
        self.assertFalse(self.task_1 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_in_later_query_set_after_archival(self, mock_schedule_archival):
        """Checks that a done routine is in the query set of later tasks after archival and not before."""
        self.assertTrue(self.task_2 in Task.objects.later())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertFalse(self.task_2 in Task.objects.later())
        archive_tasks.apply()
        self.assertTrue(self.task_2 in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_never_in_done_query_set_after_archival(self, mock_schedule_archival):
        """Checks that a reminder can never return to the set of current done tasks after archival."""
        self.assertFalse(self.task_1.id in Task.objects.done_task_ids())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(str(self.task_1.id) in Task.objects.done_task_ids())
        archive_tasks.apply()
        self.assertFalse(str(self.task_1.id) in Task.objects.done_task_ids())
        self.task_1.set_done(True)
        self.assertFalse(str(self.task_1.id) in Task.objects.current_task_ids())
        self.assertFalse(str(self.task_1.id) in Task.objects.done_task_ids())
