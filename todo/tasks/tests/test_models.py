from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from mock import patch
import redis

from ..models import Task, History
from ..tasks import archive_tasks

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
    def test_task_is_current_before_and_not_after_archival(self, mock_schedule_archival):
        """Check that a done task is current before archival and not after."""
        self.assertFalse(self.task_1.is_current())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_current())
        archive_tasks.apply()
        self.assertFalse(self.task_1.is_current())

    @patch('tasks.models.schedule_archival')
    def test_reminder_is_done_before_and_after_archival(self, mock_schedule_archival):
        """Check that a done reminder is done before and after archival."""
        self.assertFalse(self.task_1.is_done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        archive_tasks.apply()
        self.assertTrue(self.task_1.is_done())

    @patch('tasks.models.schedule_archival')
    def test_routine_is_done_before_and_not_after_archival(self, mock_schedule_archival):
        """Check that a done routine is done before archival and not after."""
        self.assertFalse(self.task_2.is_done())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2.is_done())
        archive_tasks.apply()
        self.assertFalse(self.task_2.is_done())

    @patch('tasks.models.schedule_archival')
    def test_reminder_is_never_current_after_archival(self, mock_schedule_archival):
        """Check that a reminder can never be set current after archival."""
        self.assertFalse(self.task_1.is_done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        archive_tasks.apply()
        self.assertTrue(self.task_1.is_done())
        self.task_1.set_current(True)
        self.assertFalse(self.task_1.is_current())
        self.task_1.set_done(True)
        self.assertFalse(self.task_1.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_reminder_not_done_after_archival(self, mock_schedule_archival):
        """Mark an archived reminder not done and check that it reverts to a not current, not done task."""
        self.assertFalse(self.task_1.is_done())
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_1.is_done())
        archive_tasks.apply()
        self.assertTrue(self.task_1.is_done())
        self.task_1.set_done(False)
        self.assertFalse(self.task_1.is_current())
        self.assertFalse(self.task_1.is_done())

    @patch('tasks.models.schedule_archival')
    def test_set_routine_current_after_archival(self, mock_schedule_archival):
        """Check that a routine can be marked current after archival."""
        self.assertFalse(self.task_2.is_done())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2.is_done())
        archive_tasks.apply()
        self.assertFalse(self.task_2.is_done())
        self.task_2.set_current(True)
        self.assertTrue(self.task_2.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_routine_done_after_archival(self, mock_schedule_archival):
        """Check that a routine can be marked done after archival."""
        self.assertFalse(self.task_2.is_done())
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.task_2.is_done())
        archive_tasks.apply()
        self.assertFalse(self.task_2.is_done())
        self.task_2.set_done(True)
        self.assertTrue(self.task_2.is_current())
        self.assertTrue(self.task_2.is_done())

@override_settings(
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class HistoryTest(TestCase):
    def setUp(self):
        self.task_1 = Task.objects.create(title='Task 1')
        self.task_2 = Task.objects.create(title='Task 2', is_routine=True)

    @patch('tasks.models.schedule_archival')
    def test_history_exists_after_task_archival(self, mock_schedule_archival):
        """Check that a history entry is created when a task is archived."""
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_1.history.count(), 1)

    @patch('tasks.models.schedule_archival')
    def test_reminder_done_time_is_history_done_time(self, mock_schedule_archival):
        """Check that the done time for a reminder returns the done time of its history."""
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_1.done_time(), self.task_1.history.all()[0].done_time)

    @patch('tasks.models.schedule_archival')
    def test_routine_done_time_is_latest_history_done_time(self, mock_schedule_archival):
        """Check that the done time for a routine returns the done time of its latest history."""
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_2.done_time(), self.task_2.history.all()[0].done_time)

    @patch('tasks.models.schedule_archival')
    def test_set_done_reminder_not_done_removes_history(self, mock_schedule_archival):
        """Mark a reminder as done and then not done and check that it no longer has a history."""
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.task_1.set_done(False)
        self.assertEqual(self.task_1.history.count(), 0)

    @patch('tasks.models.schedule_archival')
    def test_single_history_entry_for_reminder(self, mock_schedule_archival):
        """Archive a reminder and check that marking it done and archiving again does not create new history.
        
        Mark the other task done as well to ensure the archival occurs. Assuming correct behavior, marking \
        the reminder done after archival will not schedule another archival.

        """
        self.task_1.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.task_1.set_done(True)
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_1.history.count(), 1)

    @patch('tasks.models.schedule_archival')
    def test_multiple_history_entries_for_routine(self, mock_schedule_archival):
        """Archive a routine and check that marking it done and archiving it again creates a new history entry."""
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_2.history.count(), 1)
        self.task_2.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply()
        self.assertEqual(self.task_2.history.count(), 2)
