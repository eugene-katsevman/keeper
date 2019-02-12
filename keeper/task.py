import datetime
import os

import timespans

from keeper.settings import IGNORED_SECTIONS
from keeper.utils import days, ONE_DAY


class Task:
    def __init__(self, source=None, name="", duration=1, topic=None, topics=None,
                 at=None, till=None, periodics=None, cost=None,
                 spent=0, parent=None):

        self.source = source
        self.children = []
        self.name = name
        self.duration = duration
        self.topic = topic
        self.cost = cost
        self.periodics = periodics
        self.spent = spent
        self.parent = parent
        if parent and not self in parent.children:
            parent.children.append(self)

        self.topics = topics or []
        if topic and not topics:
            self.topics.append(topic)

        for period in periodics or []:
            period.set_task(self)

        self.at = at
        self.till = till
        self.upper_limit = None
        if self.at is not None:
            self.upper_limit = self.at
        elif self.till is not None:
            self.upper_limit = self.till

    def planned_time_to_str(self):
        if self.duration is None:
            return 'unknown'
        else:
            return str(self.duration) + 'h'

    def is_ignored(self):
        return set(self.topics).intersection(set(IGNORED_SECTIONS))

    @property
    def duration_left(self):
        return self.duration - self.spent

    def planned_upper_limit(self, date_from):
        if self.upper_limit < date_from:
            return date_from + datetime.timedelta(hours=self.duration_left)
        else:
            return self.upper_limit

    def generate_timespanset(self, start, end):
        if not self.periodics:
            return timespans.TimeSpanSet(
                timespans.TimeSpan(self.at, self.upper_limit))
        spans = []
        for period in self.periodics:
            for day in days(start.date() - ONE_DAY,
                            end.date() + ONE_DAY):
                if period.has_day(day):
                    spans.append(period.get_timespan_for_day(day))
        spanset = (timespans.TimeSpanSet(spans)
                   - timespans.TimeSpanSet(timespans.TimeSpan(None, start))
                   - timespans.TimeSpanSet(timespans.TimeSpan(end, None)))
        return spanset

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<{}> [{}] {} [{}]'.format(
            os.path.splitext(os.path.basename(self.source.filename))[0],
            self.topic, self.name, self.planned_time_to_str())

    def __repr__(self):
        return '[{}] {} [{}]'.format(
            self.topic,
            self.name,
            self.planned_time_to_str())


class Period:
    def __init__(self, start_time, specs, task=None):
        self.start_time = start_time
        self.specs = specs
        self.task = task

    def set_task(self, task):
        self.task = task

    def has_day(self, day):
        """
        :type day:datetime.date
        :param day:
        :return:
        """
        DAYS = [
            ['понедельник', 'monday'],
            ['вторник', 'tuesday'],
            ['среда', 'wednesday'],
            ['четверг', 'thursday'],
            ['пятница', 'friday'],
            ['суббота', 'saturday'],
            ['воскресенье', 'sunday']
        ]
        result = not self.specs or \
            any(d in self.specs for d in DAYS[day.weekday()])
        return result

    def get_timespan_for_day(self, day):
        start = datetime.datetime.combine(day, self.start_time)
        return timespans.TimeSpan(start=start,
                                  end=start + datetime.timedelta(hours=self.task.duration))
