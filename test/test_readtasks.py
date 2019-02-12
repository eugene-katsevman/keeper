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

