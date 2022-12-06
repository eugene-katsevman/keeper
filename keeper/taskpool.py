# -*- coding:utf-8 -*-
import dataclasses
import datetime
import itertools
import typing
from dataclasses import dataclass

import timespans

from keeper.source.parse_file import TasksSourceFile
from keeper.task import Task


@dataclass
class CheckResult:
    overdue: typing.List[Task] = dataclasses.field(default_factory=list)
    risky: typing.List[Task] = dataclasses.field(default_factory=list)
    assigned_time: float = 0
    balance: float = 0
    unbound_time: float = 0
    left: int = 0

    def mark_overdue(self, task):
        self.overdue.append(task)

    def mark_risky(self, task):
        self.risky.append(task)


class TaskPool:
    def __init__(self, task_source=None):
        self.sources = {None: TasksSourceFile()}
        if task_source:
            self.add_source(task_source)

    def add_task(self, task, first=False):
        source = None if not task.source else task.source.filename
        self.sources[source].add_task(task, first=first)

    def add_source(self, source):
        self.sources[source.filename] = source

    @property
    def tasks(self):
        tasks = []
        for s in self.sources.values():
            tasks.extend(s.tasks)
        return tasks

    @property
    def special_tasks(self):
        special_tasks = []
        for s in self.sources.values():
            special_tasks.extend(s.special_tasks)
        return special_tasks

    def today(self):
        return [task for task in self.tasks
                if task.upper_limit is not None and
                task.upper_limit.date() <= datetime.date.today()]

    def strict_at(self, date):
        return [task for task in self.tasks if task.at == date]

    def till(self, date):
        return [task for task in self.tasks
                if task.till is not None and
                task.till <= date] + self.strict_at(date)

    def periodics_duration(self, time_from: datetime.datetime,
                                 time_to: datetime.datetime) -> datetime.timedelta:
        span = timespans.TimeSpanSet()

        for t in self.tasks:
            if t.periodics:
                span += t.generate_timespanset(time_from, time_to)
        return span.duration

    def check(self, date_from: typing.Optional[datetime.datetime] = None) -> CheckResult:
        if date_from is None:
            date_from = datetime.datetime.now()

        limited_tasks = [task for task in self.tasks
                         if task.upper_limit is not None and
                         not task.periodics]
        unbound_tasks = [task for task in self.tasks
                         if task.upper_limit is None and
                         task.duration is not None and not task.periodics]
        limited_tasks.sort(
            key=lambda task: task.planned_upper_limit(date_from))

        balance = datetime.timedelta()
        now = date_from
        result = CheckResult()

        for task in limited_tasks:
            if task.upper_limit < date_from:
                result.mark_overdue(task)
            balance += task.planned_upper_limit(date_from) - now
            balance -= self.periodics_duration(now,
                                               task.planned_upper_limit(date_from))
            balance -= datetime.timedelta(hours=task.duration_left)
            if balance < datetime.timedelta():
                result.mark_risky(task)
            now = task.upper_limit
        result.assigned_time = sum(
            [datetime.timedelta(hours=task.duration_left)
             for task in limited_tasks],
            datetime.timedelta())
        result.balance = balance
        result.unbound_time = sum([datetime.timedelta(hours=task.duration_left)
                                   for task in unbound_tasks],
                                  datetime.timedelta())
        result.left = balance - result.unbound_time
        return result

    def scheduled(self) -> typing.List[Task]:
        limited_tasks = [task for task in self.tasks if task.upper_limit]
        limited_tasks.sort(key=lambda task: task.upper_limit)
        return limited_tasks

    def find_task(self, spec):
        for task in self.tasks:
            if task.name == spec:
                return task

    def find_first_to_do(self, last=None):
        def _traverse(children):
            for child in children:
                if child.is_ignored() or child.periodics:
                    continue

                result = list(_traverse(child.children))
                if not result:
                    yield child
                else:
                    yield from result

        top_level = [t for t in self.tasks if not t.parent]

        result = _traverse(top_level)
        if not last:
            return next(result)
        else:
            try:
                result = itertools.dropwhile(lambda x: x != last, result)
                next(result)
                return next(result)
            except StopIteration:
                return next(_traverse(self.tasks))
