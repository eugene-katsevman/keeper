from datetime import datetime,timedelta
from keeper.taskpool import TaskPool


def task_from_line(line):
    attributes = extract_attributes(line)
    return Task(**attributes)


def test_simple():
    tasklist = TaskPool()
    task = task_from_line('one 4h')
    tasklist.add_task(task)
    result = tasklist.check(date_from=datetime(2015, 1, 1))
    assert result.overdue == []
    assert result.risky == []
    assert result.unbound_time == timedelta(hours=4)


def test_limited():
    tasklist = TaskPool()
    task = task_from_line('one 4h [<02.01.2015]')
    tasklist.add_task(task)
    result = tasklist.check(date_from=datetime(2015, 1, 1))
    assert result.overdue == []
    assert result.risky == []
    assert result.unbound_time == timedelta(hours=0)
    assert result.balance == timedelta(hours=20)


def test_limited_with_periodics():
    tasklist = TaskPool()
    task = task_from_line('one 4h [<02.01.2015]')
    tasklist.add_task(task)
    task2 = task_from_line('two [+00:00, 21h]')
    assert task2.duration == 21
    tasklist.add_task(task2)
    result = tasklist.check(date_from=datetime(2015, 1, 1))
    assert result.overdue == []
    assert result.risky == [task]
    assert result.unbound_time == timedelta(hours=0)
    assert result.balance == timedelta(hours=-1)


def test_limited_overdue():
    tasklist = TaskPool()
    task = task_from_line('one 4h [<03.01.2015]')
    tasklist.add_task(task)

    result = tasklist.check(date_from=datetime(2015, 1, 4))
    assert result.overdue == [task]
    assert result.risky == []
    assert result.unbound_time == timedelta(hours=0)
    assert result.balance == timedelta(hours=0)


def test_limited_risky_overdue():
    tasklist = TaskPool()
    task = task_from_line('overdue 4h [<03.01.2015]')
    tasklist.add_task(task)

    task2 = task_from_line('later 2h [<04.01.2015 3:00]')
    tasklist.add_task(task2)

    result = tasklist.check(date_from=datetime(2015, 1, 4))
    assert result.overdue == [task]
    assert result.risky == [task]
    assert result.unbound_time == timedelta()
    assert result.balance == timedelta(hours=-2)


def test_timed_task():
    task = task_from_line('overdue 4ч [<03.01.2015]')
    assert task.duration == 4


def test_spent_time():
    task = task_from_line('spent 4h [spent 1h]')
    assert task.duration_left == 3
