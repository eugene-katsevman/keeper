# -*- coding:utf-8 -*-
import os
import re
import datetime
import os.path
import timespans

from keeper.settings import (HARD_PAGE_TIME,
                             EASY_PAGE_TIME,
                             IGNORED_SECTIONS,
                             APP_DIRECTORY)

strptime = datetime.datetime.strptime
ONE_DAY = datetime.timedelta(days=1)


def mkdir_p(path):
    """
    create directory {path} if necessary
    """
    if os.path.exists(path) and os.path.isdir(path):
        return

    os.makedirs(path)


def set_line(filename, lineno, line):
    with open(filename, 'r') as file:
        data = file.readlines()
    data[lineno] = line + '\n'
    with open(filename, 'w') as file:
        file.writelines(data)


def get_duration(s):
    if '?' in s:
        return None
    elif s.endswith('h') or s.endswith('ч'):
        return float(re.findall(r'\d*\.?\d+', s)[0])
    elif s.endswith('m') or s.endswith('м'):
        return float(re.findall(r'\d*\.?\d+', s)[0]) / 60


def looks_like_date(s):
    return [] != re.findall(r'^\d\d?\.\d\d?\.\d\d\d\d', s)


def looks_like_datetime(s):
    return [] != re.findall(r'^\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_time(s):
    return [] != re.findall(r'^\d\d?:\d\d?', s)


def looks_like_till_datetime(s):
    return [] != re.findall(r'^<\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_till_date(s):
    return [] != re.findall(r'^<\d\d?\.\d\d?\.\d\d\d\d', s)


def looks_like_duration(s):
    return [] != re.findall(r'^\w*\d+[hmчм]|\?[hmчм]', s)


def looks_like_spent_time(s):
    return [] != re.findall(r'spent (\d+[hmчм]|\?[hmчм])', s)


def looks_like_periodic(s):
    return s.startswith("+")


def looks_like_page_count(s):
    return [] != re.findall(r'\d+p', s)


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def days(datefrom, dateto):
    datenow = datefrom
    while datenow < dateto:
        yield datenow
        datenow += datetime.timedelta(days=1)


class Period(object):
    def __init__(self, specification=None, task=None):

        self.specification = specification[1:]
        parts = self.specification.strip().split()
        self.start_time = None
        self.specs = []
        for part in parts:
            if looks_like_time(part):
                self.start_time = strptime(part, '%H:%M').time()
            else:
                self.specs.append(part.lower())
        if not self.start_time:
            raise Exception('no start time specified for task')
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
                                  end=start +
                                  datetime.timedelta(hours=self.task.duration))


class Task:
    def __init__(self, name="", duration=1, topic=None, topics=None,
                 at=None, till=None, periodics=None, cost=None, file=None,
                 lineno=None, line=None, spent=0):
        self.taskline = TaskLine(line, lineno, file)
        self.lineno = lineno
        self.line = line
        self.name = name
        self.duration = duration
        self.topic = topic
        self.cost = cost
        self.file = file
        self.periodics = periodics
        self.spent = spent

        if self.periodics:
            for period in self.periodics:
                period.set_task(self)

        self.topics = topics or []
        if topic and not topics:
            self.topics.append(topic)

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
            os.path.splitext(os.path.basename(self.file))[0],
            self.topic, self.name, self.planned_time_to_str())

    def __repr__(self):
        return '[{}] {} [{}]'.format(
            self.topic,
            self.name,
            self.planned_time_to_str())


class Attr(object):
    def __init__(self, location, text):
        self.location = location
        self.text = text
        self.value = text.strip()

    def __repr__(self):
        return str((self.location, self.text, self.value))


class AttrCollection(object):
    def __init__(self, location, text):
        self.text = text
        self.attrs = []
        index = 0
        self.location = location
        while index < len(text):
            next_index = text.find(',', index)
            if next_index == -1:
                next_index = len(text)
            self.attrs.append(Attr(location + index, text[index:next_index]))
            index = next_index + 1

    def __repr__(self):
        return str(self.attrs)

    def is_empty(self):
        return (self.attrs == [] or
                len(self.attrs) == 1 and self.attrs[0].value == '')


class TaskLine(object):
    """
    bidirectional interface to task as stored in a file
    """
    def _parse(self):
        """
        recapture attribute collections
        :return: nothing
        """
        self.attr_collections = []
        index = self.line.find('[')
        while index != -1:
            end_index = self.line.find(']', index)
            self.attr_collections.append(
                AttrCollection(index+1, self.line[index+1:end_index]))
            index = self.line.find('[', end_index)

    @property
    def pure_name(self):
        return re.sub(r'\[.*?\]', '', self.line)

    def __init__(self, line, lineno, filename):
        self.line = line
        self.lineno = lineno
        self.filename = filename
        self._parse()

    def __str__(self):
        return "{} with attr collections ({})".format(self.line,
                                                      self.attr_collections)

    def has_attr(self, value):
        for collection in self.attr_collections:
            for attr in collection.attrs:
                if attr.value == value:
                    return True
        return False

    def set_attr(self, value):
        if not self.has_attr(value):
            self.add_attr(value)

    def add_attr(self, value):
        """
        :param value: new attribute to add to the line
        :return:
        """
        if not self.attr_collections:
            self.line += ' [{}]'.format(value)
        else:
            collection = self.attr_collections[-1]
            self.line = (self.line[:collection.location + len(collection.text)]
                         + ", " + value +
                         self.line[collection.location+len(collection.text):])
        self._parse()

    def remove_attr_by_value(self, value):
        for collection in reversed(self.attr_collections):
            for i, attr in enumerate(reversed(collection.attrs)):
                if attr.value == value:
                    self.line = (self.line[:attr.location] +
                                 self.line[attr.location+len(attr.text) +
                                           (1 if i != 0 else 0):])
        self._parse()

        for collection in reversed(self.attr_collections):
            if collection.is_empty():
                self.line = (self.line[:collection.location-1] +
                             self.line[collection.location +
                                       len(collection.text)+1:])
        self._parse()

    def save(self):
        set_line(self.filename, self.lineno, self.line)


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
    def __init__(self, filename=None):
        self.tasks = []
        self.special_tasks = []
        if filename:
            self.load_from_file(filename)

    def load_from_file(self, filename):
        current_section = None
        section_attributes = dict()
        in_comment = False
        for lineno, line in enumerate(open(filename).readlines()):
            line = line.rstrip()

            if line:
                if in_comment and "*/" in line:
                    in_comment = False
                    continue
                if in_comment:
                    continue
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('#'):
                    pass
                elif stripped.startswith("/*"):
                    in_comment = True
                elif line.endswith(':'):
                    current_section = line.strip()[:-1]
                    section_attributes = self.extract_attributes(
                        current_section)
                    current_section = re.sub(r'\[.*\]', '', current_section)
                    current_section = re.sub(r'[ ]+', ' ',
                                             current_section.strip())
                else:
                    if not line.startswith(' ') and not line.startswith('\t'):
                        current_section = None
                        section_attributes = dict()
                    attributes = dict()
                    attributes.update(section_attributes)
                    attributes.update(self.extract_attributes(line))
                    attributes['line'] = line
                    attributes['file'] = filename
                    attributes['lineno'] = lineno
                    attributes['topic'] = current_section
                    attributes['topics'] += \
                        [os.path.basename(filename).split('.')[0]]
                    if 'topics' in section_attributes:
                        attributes['topics'] += section_attributes['topics']
                    if current_section:
                        attributes['topics'].append(current_section)

                    task = Task(**attributes)
                    self.add_task(task)

    def add_task(self, task):
        if not set(task.topics).intersection(set(IGNORED_SECTIONS)):
            self.tasks.append(task)
        else:
            self.special_tasks.append(task)

    @staticmethod
    def extract_attributes(line):
        try:
            result = dict()
            result['name'] = line.strip()
            result['topics'] = []
            times = re.findall(r'\d+[чмhm]|\?[чмhm]',
                               re.sub(r'\[.*?\]', '', line))
            if times:
                time = times[0]
                result['duration'] = get_duration(time)
            attribute_line = re.findall(r'\[(.*?)\]', line)

            if attribute_line:
                attributes = [attr.strip() for attr_set in attribute_line
                              for attr in attr_set.split(',')]
                periodics = []

                for attr in attributes:
                    if looks_like_datetime(attr):
                        result['at'] = strptime(attr, '%d.%m.%Y %H:%M')
                    elif looks_like_date(attr):
                        result['at'] = strptime(attr, '%d.%m.%Y')
                    elif looks_like_spent_time(attr):
                        result['spent'] = get_duration(attr)
                    elif looks_like_duration(attr):
                        result['duration'] = get_duration(attr)
                    elif looks_like_till_datetime(attr):
                        result['till'] = strptime(attr[1:], '%d.%m.%Y %H:%M')
                    elif looks_like_till_date(attr):
                        result['till'] = strptime(attr[1:], '%d.%m.%Y')
                    elif looks_like_periodic(attr):
                        periodics.append(Period(attr))
                    elif attr.startswith('$') or attr.startswith("р"):
                        result['cost'] = float(attr[2:])
                        result['topics'].append('money')
                    elif attr == 'today':
                        today_date = datetime.datetime.now().date()
                        today_datetime = datetime.datetime.combine(today_date,
                                                             datetime.time(0))
                        tomorrow = today_datetime + ONE_DAY
                        result['till'] = tomorrow
                    elif looks_like_page_count(attr):
                        page_count = int(attr[:-1])
                        result['topics'].append("books")
                        if "hard" in attributes:
                            result['duration'] = page_count * HARD_PAGE_TIME
                        else:
                            result['duration'] = page_count * EASY_PAGE_TIME
                    else:
                        result['topics'].append(attr)
                result['periodics'] = periodics
            return result
        except Exception as e:
            raise Exception("error while parsing {}: {}".format(line, str(e)))

    def task_from_line(self, line):

        attributes = self.extract_attributes(line)
        attributes['line'] = line
        return Task(**attributes)

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


def load_all():
    task_pool = TaskList()
    lists_dir = APP_DIRECTORY
    for filename in os.listdir(lists_dir):
        if filename.endswith('.todo'):
            task_pool.load_from_file(os.path.join(lists_dir, filename))
    return task_pool
