# -*- coding:utf-8 -*-
import datetime
import itertools

import timespans

from keeper.source import TaskSource


class CheckResult:
    def __init__(self):
        self._overdue = []
        self._risky = []
        self.assigned_time = 0
        self.balance = 0
        self.unbound_time = 0
        self.left = 0

    def overdue(self, task):
        self._overdue.append(task)

    def risky(self, task):
        self._risky.append(task)


class TaskList:
    def __init__(self, task_source=None):
        self.sources = {None: TaskSource()}
        if task_source:
            self.add_source(task_source)

    def add_task(self, task):
        source = None if not task.source else task.source.filename
        self.sources[source].add_task(task)

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

    def special_time(self, time_from, time_to):
        span = timespans.TimeSpanSet()

        for t in self.tasks:
            if t.periodics:
                span += t.generate_timespanset(time_from, time_to)
        return span.duration

    def _check(self, date_from=None):
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
                result.overdue(task)
            balance += task.planned_upper_limit(date_from) - now
            balance -= self.special_time(now,
                                         task.planned_upper_limit(date_from))
            balance -= datetime.timedelta(hours=task.duration_left)
            if balance < datetime.timedelta():
                result.risky(task)
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

    def check(self, date_from=None):
        def td_to_hours(td):
            """
            :type td: timedelta
            """
            day_hours = td.days * 24
            full_hours = int(float(td.seconds) / 3600)
            remaining_hours = float(td.seconds % 3600) / 3600
            hours = (day_hours + full_hours + remaining_hours)
            return round(hours, 2)

        result = self._check(date_from)
        print('Assigned time (how long limited tasks will take):'.ljust(50),
              td_to_hours(result.assigned_time))
        print('Balance (time total balance for limited tasks):'.ljust(50),
              td_to_hours(result.balance))
        print('Unbound time (how long free tasks will take):'.ljust(50),
              td_to_hours(result.unbound_time))
        # (Can we do both limited and free tasks?)
        print('Free time left till latest limited task:'.ljust(50),
              td_to_hours(result.left))
        if result.left.total_seconds() < 0:
            print('You\'re short of time. Either limit some unbound tasks,'
                  ' or postpone some of limited',)
        print()
        if not result._overdue and not result._risky:
            print('We\'re good')
        else:
            for task in result._overdue:
                print('OVERDUE', task)
            for task in result._risky:
                print('RISKY', task)

    def scheduled(self, date_from=None):
        if date_from is None:
            date_from = datetime.datetime.now()
        limited_tasks = [task for task in self.tasks if task.upper_limit]
        limited_tasks.sort(key=lambda task: task.upper_limit)
        for task in limited_tasks:
            print(task)

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
