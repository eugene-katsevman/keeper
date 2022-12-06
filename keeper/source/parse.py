import datetime
import re
import typing

from keeper.settings import HARD_PAGE_TIME, EASY_PAGE_TIME
from keeper.settings import TIME_POOLS

from keeper.source.abstract import Periodic

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


def get_indent_level(line):
    return len(line) - len(line.lstrip())


def extract_periodics(attr) -> Periodic:
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
    return Periodic(start_time, specs)


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
                    periodics.append(extract_periodics(attr))
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
                elif attr in TIME_POOLS:
                    result['timepool'] = attr
                else:
                    result['topics'].append(attr)
            result['periodics'] = periodics
        return result
    except Exception as e:
        raise Exception("error while parsing {}: {}".format(line, str(e)))





