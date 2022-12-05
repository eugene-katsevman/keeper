import datetime
import os
import re
import typing

from keeper.settings import HARD_PAGE_TIME, EASY_PAGE_TIME

from keeper.task import Task, Period

from keeper.utils import ONE_DAY

strptime = datetime.datetime.strptime


def set_line(filename: str, lineno: int, line: str):
    with open(filename, 'r') as file:
        data = file.readlines()
    data[lineno] = line + '\n'
    with open(filename, 'w') as file:
        file.writelines(data)


def get_duration(s: str):
    if '?' in s:
        return None
    elif s.endswith('h') or s.endswith('ч'):
        return float(re.findall(r'\d*\.?\d+', s)[0])
    elif s.endswith('m') or s.endswith('м'):
        return float(re.findall(r'\d*\.?\d+', s)[0]) / 60


def looks_like_date(s: str):
    return [] != re.findall(r'^\d\d?\.\d\d?\.\d\d\d\d', s)


def looks_like_datetime(s: str):
    return [] != re.findall(r'^\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_time(s: str):
    return [] != re.findall(r'^\d\d?:\d\d?', s)


def looks_like_till_datetime(s: str):
    return [] != re.findall(r'^<\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_till_date(s: str):
    return [] != re.findall(r'^<\d\d?\.\d\d?\.\d\d\d\d', s)


def looks_like_duration(s: str):
    return [] != re.findall(r'^\w*\d+[hmчм]|\?[hmчм]', s)


def looks_like_spent_time(s: str):
    return [] != re.findall(r'spent (\d+[hmчм]|\?[hmчм])', s)


def looks_like_periodic(s: str):
    return s.startswith("+")


def looks_like_page_count(s: str):
    return [] != re.findall(r'\d+p', s)


def is_number(s: str):
    try:
        int(s)
        return True
    except ValueError:
        return False


class Attribute:
    """
    Single attribute inside [] brackets
    """
    def __init__(self, location, text):
        self.location = location
        self.text = text
        self.value = text.strip()

    def __repr__(self):
        return str((self.location, self.text, self.value))


class Attributes:
    """
    A collection of comma-separated attributes inside [] brackets
    """
    def __init__(self, location, text):
        """
        Split attributes into separate Attr classes
        :param location: where collection starts in the line
        :param text: what lies between the brackets
        """
        self.text = text
        self.attrs = []
        self.location = location
        index = 0
        while index < len(text):
            next_index = text.find(',', index)
            if next_index == -1:
                next_index = len(text)
            self.attrs.append(Attribute(location + index, text[index:next_index]))
            index = next_index + 1

    def __getitem__(self, item):
        return self.attrs[item]

    def __repr__(self):
        return str(self.attrs)

    def is_empty(self):
        return (self.attrs == [] or
                len(self.attrs) == 1 and self.attrs[0].value == '')

    def __bool__(self):
        return not self.is_empty()


class SourceLine:
    """
    Single source file representation
    """
    def _parse(self):
        pass

    def __init__(self, line):
        self.line = line
        self._parse()


class TaskLine(SourceLine):
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
                Attributes(index + 1, self.line[index + 1:end_index]))
            index = self.line.find('[', end_index)

    @property
    def pure_name(self):
        return re.sub(r'\[.*?\]', '', self.line)

    def __init__(self, line, source=None):
        SourceLine.__init__(self, line)
        self.source = source

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
        self.source.save()


def task_from_line(line):
    attributes = extract_attributes(line)
    return Task(**attributes)


def get_level(line):
    return len(line) - len(line.lstrip())


def extract_period(attr):
    specification = attr[1:]
    parts = specification.strip().split()
    start_time = None
    specs = []
    for part in parts:
        if looks_like_time(part):
            start_time = strptime(part, '%H:%M').time()
        else:
            specs.append(part.lower())
    if not start_time:
        raise Exception('no start time specified for task')
    return Period(start_time, specs)


# todo: typed dict
def extract_attributes(line: str) -> typing.Dict[str, typing.Any]:
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
                    periodics.append(extract_period(attr))
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


class TaskTuple(typing.NamedTuple):
    level: int
    task: Task


class TaskSource:
    def __init__(self, filename=None, stream=None):
        self.tasks = []
        self.special_tasks = []
        self.lines = []
        self.filename = filename
        if stream:
            self._load_from_stream(stream, filename=filename)
        elif filename:
            self._load_from_file(filename)

    def _load_from_stream(self, stream, filename=None):
        task_stack = []
        current_section = None
        section_attributes = dict()
        in_comment = False
        prev_level, level = 0, 0
        self.lines = [SourceLine(line.rstrip()) for line in stream.readlines()]
        for lineno, source_line in enumerate(self.lines):
            line = source_line.line
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
                    section_attributes = extract_attributes(current_section)
                    current_section = re.sub(r'\[.*\]', '', current_section)
                    current_section = re.sub(r'[ ]+', ' ',
                                             current_section.strip())
                else:
                    prev_level, level = level, get_level(line)
                    if not level:
                        current_section = None
                        section_attributes = dict()

                    taskline = TaskLine(line, source=self)
                    attributes = dict()
                    attributes.update(section_attributes)
                    attributes.update(extract_attributes(line))
                    attributes['topic'] = current_section
                    attributes['topics'] += \
                        [os.path.basename(filename).split('.')[0]]

                    attributes['topics'] += section_attributes.get('topics', [])
                    if current_section:
                        attributes['topics'].append(current_section)

                    attributes['source'] = taskline
                    while task_stack and task_stack[-1].level >= level:
                        task_stack.pop(-1)
                    attributes['parent'] = None if not task_stack else task_stack[-1].task

                    task = Task(**attributes)

                    self.add_task(task)
                    self.lines[lineno] = taskline
                    task_stack.append(TaskTuple(level=level, task=task))

    def _load_from_file(self, filename):
        with open(filename) as f:
            self._load_from_stream(stream=f, filename=filename)

    def save(self):
        with open(self.filename, 'w') as f:
            f.writelines(source_line.line + '\n' for source_line in self.lines)

    def add_task(self, task, first=False):
        if task.is_ignored():
            if not first:
                self.special_tasks.append(task)
            else:
                self.special_tasks.insert(0, task)
        else:
            if not first:
                self.tasks.append(task)
            else:
                self.tasks.insert(0, task)

    def insert_after(self, line, after):
        line.source = self
        self.lines.insert(after + 1, line)

    def insert_before(self, line, before):
        line.source = self
        self.lines.insert(before, line)
