from datetime import datetime,timedelta
from keeper.tasklist import TaskList
from keeper.source import task_from_line
from keeper.common import add_child


def test_simple():
    tasklist = TaskList()
    task = task_from_line('one 4h')
    tasklist.add_task(task)
    result = tasklist._check(date_from=datetime(2015, 1, 1))
    assert result._overdue == []
    assert result._risky == []
    assert result.unbound_time == timedelta(hours=4)


def test_limited():
    tasklist = TaskList()
    task = task_from_line('one 4h [<02.01.2015]')
    tasklist.add_task(task)
    result = tasklist._check(date_from=datetime(2015, 1, 1))
    assert result._overdue == []
    assert result._risky == []
    assert result.unbound_time == timedelta(hours=0)
    assert result.balance == timedelta(hours=20)


def test_limited_with_periodics():
    tasklist = TaskList()
    task = task_from_line('one 4h [<02.01.2015]')
    tasklist.add_task(task)
    task2 = task_from_line('two [+00:00, 21h]')
    assert task2.duration == 21
    tasklist.add_task(task2)
    result = tasklist._check(date_from=datetime(2015, 1, 1))
    assert result._overdue == []
    assert result._risky == [task]
    assert result.unbound_time == timedelta(hours=0)
    assert result.balance == timedelta(hours=-1)


def test_limited_overdue():
    tasklist = TaskList()
    task = task_from_line('one 4h [<03.01.2015]')
    tasklist.add_task(task)

    result = tasklist._check(date_from=datetime(2015, 1, 4))
    assert result._overdue == [task]
    assert result._risky == []
    assert result.unbound_time == timedelta(hours=0)
    assert result.balance == timedelta(hours=0)


def test_limited_risky_overdue():
    tasklist = TaskList()
    task = task_from_line('overdue 4h [<03.01.2015]')
    tasklist.add_task(task)

    task2 = task_from_line('later 2h [<04.01.2015 3:00]')
    tasklist.add_task(task2)

    result = tasklist._check(date_from=datetime(2015, 1, 4))
    assert result._overdue == [task]
    assert result._risky == [task]
    assert result.unbound_time == timedelta()
    assert result.balance == timedelta(hours=-2)


def test_timed_task():
    task = task_from_line('overdue 4ч [<03.01.2015]')
    assert task.duration == 4


def test_task_root():
    root = TaskList().root

    root.add_child(task_from_line('spent 4h [spent 1h]'))
    root.add_child(task_from_line('spent 4h [spent 1h]'))

    assert len(root.children) == 2
