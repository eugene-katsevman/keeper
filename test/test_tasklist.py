from unittest import TestCase
from datetime import datetime,timedelta
from keeper.tasks import TaskList, Task


class TaskListTestCase(TestCase):
    def test_simple(self):
        tasklist = TaskList()
        task = tasklist.task_from_line('one 4h')
        tasklist.add_task(task)
        result = tasklist._check(date_from=datetime(2015, 1, 1))
        self.assertEqual(result._overdue, [])
        self.assertEqual(result._risky, [])
        self.assertEqual(result.unbound_time, timedelta(hours=4))

    def test_limited(self):
        tasklist = TaskList()
        task = tasklist.task_from_line('one 4h [<02.01.2015]')
        tasklist.add_task(task)
        result = tasklist._check(date_from=datetime(2015, 1, 1))
        self.assertEqual(result._overdue, [])
        self.assertEqual(result._risky, [])
        self.assertEqual(result.unbound_time, timedelta(hours=0))
        self.assertEqual(result.balance, timedelta(hours=20))

    def test_limited_with_periodics(self):
        tasklist = TaskList()
        task = tasklist.task_from_line('one 4h [<02.01.2015]')
        tasklist.add_task(task)
        task2 = tasklist.task_from_line('one 4h [+00:00, 21h]')
        tasklist.add_task(task2)
        result = tasklist._check(date_from=datetime(2015, 1, 1))
        self.assertEqual(result._overdue, [])
        self.assertEqual(result._risky, [task])
        self.assertEqual(result.unbound_time, timedelta(hours=0))
        self.assertEqual(result.balance, timedelta(hours=-1))

    def test_limited_overdue(self):
        tasklist = TaskList()
        task = tasklist.task_from_line('one 4h [<03.01.2015]')
        tasklist.add_task(task)

        result = tasklist._check(date_from=datetime(2015, 1, 4))
        self.assertEqual(result._overdue, [task])
        self.assertEqual(result._risky, [])
        self.assertEqual(result.unbound_time, timedelta(hours=0))
        self.assertEqual(result.balance, timedelta(hours=0))

    def test_limited_risky_overdue(self):
        tasklist = TaskList()
        task = tasklist.task_from_line('overdue 4h [<03.01.2015]')
        tasklist.add_task(task)

        task2 = tasklist.task_from_line('later 2h [<04.01.2015 3:00]')
        tasklist.add_task(task2)

        result = tasklist._check(date_from=datetime(2015, 1, 4))
        self.assertEqual(result._overdue, [task])
        self.assertEqual(result._risky, [task])
        self.assertEqual(result.unbound_time, timedelta())
        self.assertEqual(result.balance, timedelta(hours=-2))


    def test_timed_task(self):
        tasklist = TaskList()
        task = tasklist.task_from_line('overdue 4ч [<03.01.2015]')
        self.assertEqual(task.length, 4)
