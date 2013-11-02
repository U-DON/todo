from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
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
class TaskManagerTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', name='test', password='test')
        self.reminder = self.user.tasks.create(title='Reminder')
        self.routine = self.user.tasks.create(title='Routine', is_routine=True)

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def test_current_reminder_in_current_query_set(self):
        """Marks a reminder as current and checks that it's in the query set of current but not later tasks."""
        self.assertFalse(self.reminder in Task.objects.current())
        self.assertTrue(self.reminder in Task.objects.later())
        self.reminder.set_current(True)
        self.assertTrue(self.reminder in Task.objects.current())
        self.assertFalse(self.reminder in Task.objects.later())

    def test_current_routine_in_current_query_set(self):
        """Marks a routine as current and checks that it's in the query set of current but not later tasks."""
        self.assertFalse(self.routine in Task.objects.current())
        self.assertTrue(self.routine in Task.objects.later())
        self.routine.set_current(True)
        self.assertTrue(self.routine in Task.objects.current())
        self.assertFalse(self.routine in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_in_done_query_set(self, mock_schedule_archival):
        """Marks a reminder done and checks that it's in the query sets of done and current but not later tasks."""
        self.assertFalse(self.reminder in Task.objects.done())
        self.assertTrue(self.reminder in Task.objects.later())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder in Task.objects.done())
        self.assertFalse(self.reminder in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_in_done_query_set(self, mock_schedule_archival):
        """Marks a routine done and checks that it's in the query sets of done and current but not later tasks."""
        self.assertFalse(self.routine in Task.objects.done())
        self.assertTrue(self.routine in Task.objects.later())
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.routine in Task.objects.done())
        # Note that archival has not happened as this point, so task should still be current.
        self.assertFalse(self.routine in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_and_routine_in_done_query_set(self, mock_schedule_archival):
        """Marks a reminder and a routine done and checks that both are in the query set of done tasks."""
        self.assertFalse(self.reminder in Task.objects.done())
        self.assertFalse(self.routine in Task.objects.done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder in Task.objects.done())
        self.assertFalse(self.reminder in Task.objects.later())
        self.assertTrue(self.routine in Task.objects.done())
        self.assertFalse(self.routine in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_in_done_query_set_before_and_after_archival(self, mock_schedule_archival):
        """Checks that a done reminder is in the query set of done tasks before and after archival."""
        self.assertFalse(self.reminder in Task.objects.done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder in Task.objects.done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertTrue(self.reminder in Task.objects.done())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_not_in_done_query_set_after_archival(self, mock_schedule_archival):
        """Checks that a done routine is in the query set of done tasks before archival and not after."""
        self.assertFalse(self.routine in Task.objects.done())
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.routine in Task.objects.done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertFalse(self.routine in Task.objects.done())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_not_in_later_query_set_before_or_after_archival(self, mock_schedule_archival):
        """Checks that a done reminder is not in the query set of later tasks before or after archival."""
        self.assertTrue(self.reminder in Task.objects.later())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertFalse(self.reminder in Task.objects.later())
        archive_tasks.apply(args=[self.user.pk])
        self.assertFalse(self.reminder in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_routine_in_later_query_set_after_archival(self, mock_schedule_archival):
        """Checks that a done routine is in the query set of later tasks after archival and not before."""
        self.assertTrue(self.routine in Task.objects.later())
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertFalse(self.routine in Task.objects.later())
        archive_tasks.apply(args=[self.user.pk])
        self.assertTrue(self.routine in Task.objects.later())

    @patch('tasks.models.schedule_archival')
    def test_done_reminder_never_in_done_query_set_after_archival(self, mock_schedule_archival):
        """Checks that a reminder can never return to the set of current done tasks after archival."""
        self.assertFalse(self.reminder.id in Task.objects.done_task_ids())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(str(self.reminder.id) in Task.objects.done_task_ids())
        archive_tasks.apply(args=[self.user.pk])
        self.assertFalse(str(self.reminder.id) in Task.objects.done_task_ids())
        self.reminder.set_done(True)
        self.assertFalse(str(self.reminder.id) in Task.objects.current_task_ids())
        self.assertFalse(str(self.reminder.id) in Task.objects.done_task_ids())

@override_settings(
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class TaskTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', name='test', password='test')
        self.reminder = self.user.tasks.create(title='Reminder')
        self.routine = self.user.tasks.create(title='Routine', is_routine=True)

    def tearDown(self):
        redis.StrictRedis(connection_pool=settings.REDIS_POOL).flushdb()

    def test_set_task_current(self):
        """Marks a task as current and checks that it's current."""
        self.assertFalse(self.reminder.is_current())
        self.reminder.set_current(True)
        self.assertTrue(self.reminder.is_current())

    def test_set_current_task_not_current(self):
        """Marks a current task as not current and checks that it's not current."""
        self.reminder.set_current(True)
        self.assertTrue(self.reminder.is_current())
        self.reminder.set_current(False)
        self.assertFalse(self.reminder.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_task_done(self, mock_schedule_archival):
        """Marks a task as done and checks that it's done and current."""
        self.assertFalse(self.reminder.is_done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_done())
        self.assertTrue(self.reminder.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_done_task_not_done(self, mock_schedule_archival):
        """Marks a done task as not done and checks that it's not done and still current."""
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_done())
        self.assertTrue(self.reminder.is_current())
        self.reminder.set_done(False)
        self.assertFalse(self.reminder.is_done())
        self.assertTrue(self.reminder.is_current())

    @patch('tasks.models.schedule_archival')
    def test_get_task_done_time(self, mock_schedule_archival):
        """Checks that the done time of the task is the current time, both in UTC and accurate to the minute."""
        self.assertFalse(self.reminder.is_done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_done())
        self.assertEqual(
            self.reminder.done_time().replace(second=0, microsecond=0),
            timezone.utc.localize(datetime.utcnow()).replace(second=0, microsecond=0)
        )

    @patch('tasks.models.schedule_archival')
    def test_task_is_current_before_and_not_after_archival(self, mock_schedule_archival):
        """Checks that a done task is current before archival and not after."""
        self.assertFalse(self.reminder.is_current())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_current())
        archive_tasks.apply(args=[self.user.pk])
        print redis.StrictRedis(connection_pool=settings.REDIS_POOL).hvals('user#{user_id}'.format(user_id=self.user.pk))
        self.assertFalse(self.reminder.is_current())

    @patch('tasks.models.schedule_archival')
    def test_reminder_is_done_before_and_after_archival(self, mock_schedule_archival):
        """Checks that a done reminder is done before and after archival."""
        self.assertFalse(self.reminder.is_done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertTrue(self.reminder.is_done())

    @patch('tasks.models.schedule_archival')
    def test_routine_is_done_before_and_not_after_archival(self, mock_schedule_archival):
        """Checks that a done routine is done before archival and not after."""
        self.assertFalse(self.routine.is_done())
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.routine.is_done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertFalse(self.routine.is_done())

    @patch('tasks.models.schedule_archival')
    def test_reminder_is_never_current_after_archival(self, mock_schedule_archival):
        """Checks that a reminder can never be set current after archival."""
        self.assertFalse(self.reminder.is_done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertTrue(self.reminder.is_done())
        self.reminder.set_current(True)
        self.assertFalse(self.reminder.is_current())
        self.reminder.set_done(True)
        self.assertFalse(self.reminder.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_reminder_not_done_after_archival(self, mock_schedule_archival):
        """Marks an archived reminder not done and checks that it reverts to a not current, not done task."""
        self.assertFalse(self.reminder.is_done())
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.reminder.is_done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertTrue(self.reminder.is_done())
        self.reminder.set_done(False)
        self.assertFalse(self.reminder.is_current())
        self.assertFalse(self.reminder.is_done())

    @patch('tasks.models.schedule_archival')
    def test_set_routine_current_after_archival(self, mock_schedule_archival):
        """Checks that a routine can be marked current after archival."""
        self.assertFalse(self.routine.is_done())
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.routine.is_done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertFalse(self.routine.is_done())
        self.routine.set_current(True)
        self.assertTrue(self.routine.is_current())

    @patch('tasks.models.schedule_archival')
    def test_set_routine_done_after_archival(self, mock_schedule_archival):
        """Checks that a routine can be marked done after archival."""
        self.assertFalse(self.routine.is_done())
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        self.assertTrue(self.routine.is_done())
        archive_tasks.apply(args=[self.user.pk])
        self.assertFalse(self.routine.is_done())
        self.routine.set_done(True)
        self.assertTrue(self.routine.is_current())
        self.assertTrue(self.routine.is_done())

@override_settings(
    REDIS_POOL = redis.ConnectionPool(**settings.TEST_REDIS_CONF)
)
class HistoryTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', name='test', password='test')
        self.reminder = self.user.tasks.create(title='Reminder')
        self.routine = self.user.tasks.create(title='Routine', is_routine=True)

    @patch('tasks.models.schedule_archival')
    def test_history_exists_after_task_archival(self, mock_schedule_archival):
        """Checks that a history entry is created when a task is archived."""
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.assertEqual(self.reminder.history.count(), 1)

    @patch('tasks.models.schedule_archival')
    def test_reminder_done_time_is_history_done_time(self, mock_schedule_archival):
        """Checks that the done time for a reminder returns the done time of its history."""
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.assertEqual(self.reminder.done_time(), self.reminder.history.all()[0].done_time)

    @patch('tasks.models.schedule_archival')
    def test_routine_done_time_is_latest_history_done_time(self, mock_schedule_archival):
        """Checks that the done time for a routine returns the done time of its latest history."""
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.assertEqual(self.routine.done_time(), self.routine.history.all()[0].done_time)

    @patch('tasks.models.schedule_archival')
    def test_set_done_reminder_not_done_removes_history(self, mock_schedule_archival):
        """Marks a reminder as done and then not done and checks that it no longer has a history."""
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.reminder.set_done(False)
        self.assertEqual(self.reminder.history.count(), 0)

    @patch('tasks.models.schedule_archival')
    def test_single_history_entry_for_reminder(self, mock_schedule_archival):
        """Archives a reminder and checks that marking it done and archiving again does not create new history.
        
        Marks the other task done as well to ensure the archival occurs. Assuming correct behavior, marking \
        the reminder done after archival will not schedule another archival.

        """
        self.reminder.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.reminder.set_done(True)
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.assertEqual(self.reminder.history.count(), 1)

    @patch('tasks.models.schedule_archival')
    def test_multiple_history_entries_for_routine(self, mock_schedule_archival):
        """Archives a routine and checks that marking it done and archiving it again creates a new history entry."""
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.assertEqual(self.routine.history.count(), 1)
        self.routine.set_done(True)
        mock_schedule_archival.assert_called_once()
        archive_tasks.apply(args=[self.user.pk])
        self.assertEqual(self.routine.history.count(), 2)
