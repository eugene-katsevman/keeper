# -*- coding:utf-8 -*-
import os
import re
import datetime
import os.path
import platform
import errno
import timespans
from .settings import *

WINDOWS = platform.system() == 'Windows'


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def set_line(filename, lineno, line):
    with open(filename, 'r') as file:
        data = file.readlines()
    data[lineno] = line + '\n'
    with open(filename, 'w') as file:
        file.writelines( data )

    
    
def get_dir():
    return os.path.expanduser('~/.keeper')+'/'

def get_length(s):
    if '?' in s:
        return None
    elif s.endswith('h') or s.endswith('ч'):
        return float(re.findall('\d*\.?\d+', s)[0])
    elif s.endswith('m') or s.endswith('м'):
        return float(re.findall('\d*\.?\d+', s)[0]) / 60

def looks_like_date(s):
    return [] != re.findall('^\d\d?\.\d\d?\.\d\d\d\d', s)

def looks_like_datetime(s):
    return [] != re.findall('^\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)

def looks_like_time(s):
    return [] != re.findall('^\d\d?:\d\d?', s)

def looks_like_till_datetime(s):
    return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_till_date(s):
    return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d', s)

def looks_like_length(s):
    return [] != re.findall('\d+[hmчм]|\?[hmчм]', s)

def looks_like_periodic(s):
    return s.startswith("+")

def looks_like_page_count(s):
    return [] != re.findall('\d+p', s)

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
        datenow += datetime.timedelta(days = 1)


class Period(object):
    def __init__(self, specification = None, task = None):

        self.specification = specification[1:]
        parts = self.specification.strip().split()
        self.start_time = None
        self.specs = []
        for part in parts:
            if looks_like_time(part):
                self.start_time = datetime.datetime.strptime(part, '%H:%M').time()
            else:
                self.specs.append(part)
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
        result = not self.specs or \
            any(d in self.specs for d in ["понедельник", 'Monday', 'monday'])and day.weekday() == 0 or \
            any(d in self.specs for d in ["вторник",'Tuesday', 'tuesday']) and day.weekday() == 1 or \
            any(d in self.specs for d in ["среда",'Wednesday', 'wednesday']) and day.weekday() == 2 or \
            any(d in self.specs for d in ["четверг",'Thursday', 'thursday'])  and day.weekday() == 3 or \
            any(d in self.specs for d in ["пятница",'Friday', 'friday'])  and day.weekday() == 4 or \
            any(d in self.specs for d in ["суббота",'Saturday', 'saturday'])  and day.weekday() == 5 or \
            any(d in self.specs for d in ["воскресенье",'Sunday', 'sunday']) and day.weekday() == 6
        return result

    def get_timespan_for_day(self, day):
        start = datetime.datetime.combine(day, self.start_time)
        return timespans.TimeSpan(start=start,
                                  end=start + datetime.timedelta(hours=self.task.length))

class Task:
    def __init__(self, name = "", length = 1, topic = None, topics = [], at = None, till = None, periodics = None, cost = None, file=None, lineno=None, line=None):
        self.taskline = TaskLine(line, lineno, file)
        self.lineno = lineno
        self.line = line
        self.name = name
        self.length = length
        self.topic = topic
        self.cost = cost
        self.file = file
        self.periodics = periodics
        if self.periodics:
            for period in self.periodics:
                period.set_task(self)

        self.topics = topics
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
        if self.length is None:
            return 'unknown'
        else:
            return str(self.length) + 'h'


    def generate_timespanset(self, start, end):
        if not self.periodics:
            return timespans.TimeSpanSet(timespans.TimeSpan(self.at, self.upper_limit))
        spans = []
        for period in self.periodics:
            for day in days(start.date() - datetime.timedelta(days=1), end.date()+datetime.timedelta(days=1)):
                if period.has_day(day):
                    spans.append(period.get_timespan_for_day(day))
        spanset = (timespans.TimeSpanSet(spans)
                  -timespans.TimeSpanSet(timespans.TimeSpan(None, start))
                  -timespans.TimeSpanSet(timespans.TimeSpan(end, None)))
        return spanset.converge()

    def __str__(self):        
        return self.__unicode__()

    def __unicode__(self):

        if not WINDOWS:
            return "<{}> [{}] {} [{}]".format(os.path.splitext(os.path.basename(self.file))[0], self.topic, self.name, self.planned_time_to_str())
        else:
            topic = self.topic
            if not topic:
                topic = "None"
            return "<{}> [{}] {} [{}]".format(os.path.splitext(os.path.basename(self.file))[0], topic.encode("cp866"), self.name.encode('cp866'), self.planned_time_to_str().encode('cp866'))
        

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
            self.attrs.append(Attr(location + index, text[index:next_index] ))
            index = next_index + 1
    def __repr__(self):
        return str(self.attrs)

    def is_empty(self):
        return self.attrs == [] or len(self.attrs) == 1 and self.attrs[0].value == ''

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
            self.attr_collections.append(AttrCollection(index+1, self.line[index+1:end_index]))
            index = self.line.find('[', end_index)

    def __init__(self, line, lineno, filename):
        self.line = line
        self.lineno = lineno
        self.filename = filename
        self._parse()

    def __str__(self):
        return "{} with attr collections ({})".format(self.line, self.attr_collections)


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
        if self.attr_collections == []:
            self.line += ' [{}]'.format(value)
        else:
            collection = self.attr_collections[-1]
            self.line = self.line[:collection.location+len(collection.text)] + ", " + value + \
                self.line[collection.location+len(collection.text) :]
        self._parse()

    def remove_attr_by_value(self, value):
        for collection in reversed(self.attr_collections):
            for i, attr in enumerate(reversed(collection.attrs)):
                if attr.value == value:
                    self.line = self.line[:attr.location]+self.line[attr.location+len(attr.text)+ (1 if i!=0 else 0):]
        self._parse()

        for collection in reversed(self.attr_collections):
            if collection.is_empty():
                self.line = self.line[:collection.location-1]+self.line[collection.location+len(collection.text)+1:]
        self._parse()

    def save(self):
        set_line(self.filename, self.lineno, self.line)

class TaskList:
    def __init__(self, filename = None):
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
            if WINDOWS:                
                line = line.decode('windows-1251')
                
            if line:
                if in_comment and "*/" in line:
                  in_comment = False
                  continue
                if in_comment:
                    continue
                if line.strip().startswith('//') or line.strip().startswith('#'):
                    pass
                elif line.strip().startswith("/*"):
                    in_comment = True
                elif line.endswith(':'):
                    current_section = line.strip()[:-1]
                    section_attributes = self.extract_attributes(current_section)
                    current_section = re.sub('\[.*\]', '', current_section)
                    current_section = re.sub('[ ]+', ' ', current_section.strip())

                else:
                    attributes = dict()
                    if not line.startswith(' ') and not line.startswith('\t'):
                        current_section = None
                        section_attributes = dict()
                    attributes.update(section_attributes)
                    attributes.update(self.extract_attributes(line))
                    attributes['line'] = line
                    attributes['file'] = filename
                    attributes['lineno'] = lineno
                    attributes['topic'] = current_section
                    attributes['topics'] += [os.path.basename(filename).split('.')[0]]
                    if 'topics' in section_attributes:
                        attributes['topics'] += section_attributes['topics']
                    if current_section:
                        attributes['topics'].append(current_section)

                    task = Task(**attributes)
                    if not set(attributes['topics']).intersection(set(IGNORED_SECTIONS)):
                        self.tasks.append(task)
                    else:
                        self.special_tasks.append(task)

    @staticmethod
    def extract_attributes(line):
        try:
            result = dict()
            result['name'] = line.strip()
            result['topics'] = []
            times = re.findall('\d+[hm]|\?[hm]', line)
            if times:
                time = times[0]
                result['length'] = get_length(time)
            attribute_line = re.findall('\[(.*?)\]', line)

            if attribute_line:
                attributes = [attr.strip() for attr_set in attribute_line for attr in attr_set.split(',')]
                periodics = []

                for attr in attributes:
                    if looks_like_datetime(attr):
                        result['at'] = datetime.datetime.strptime(attr, '%d.%m.%Y %H:%M')
                    elif looks_like_date(attr):
                        result['at'] = datetime.datetime.strptime(attr, '%d.%m.%Y')
                    elif looks_like_length(attr):
                        result['length'] = get_length(attr)              
                    elif looks_like_till_datetime(attr):
                        result['till'] = datetime.datetime.strptime(attr[1:], '%d.%m.%Y %H:%M')
                    elif looks_like_till_date(attr):
                        result['till'] = datetime.datetime.strptime(attr[1:], '%d.%m.%Y')
                    elif looks_like_periodic(attr):
                        periodics.append(Period(attr))
                    elif attr.startswith('$') or attr.startswith("р"):

                        result['cost'] = float(attr[2:])
                        result['topics'].append('money')
                    elif looks_like_page_count(attr):
                        page_count = int(attr[:-1])
                        result['topics'].append("books")
                        if "hard" in attributes:
                            result['length'] = page_count * HARD_PAGE_TIME
                        else:
                            result['length'] = page_count * SIMPLE_PAGE_TIME
                    else:
                        result['topics'].append(attr)        
                result['periodics'] = periodics
            return result                        
        except Exception as e:
            raise Exception("error while parsing {}: ".format(line) + e.message)

    def today(self):
        return [task for task in self.tasks if task.upper_limit is not None and task.upper_limit.date()<=datetime.date.today()]
        
    def strict_at(self, date):
        return [task for task in self.tasks if task.at == date]
    
    def till(self, date):
        return [task for task in self.tasks if task.till != None and task.till<=date] + self.strict_at(date)

    def is_sleeping_time(self, time):
        start_sleep = datetime.datetime.combine(time.date(), datetime.time(hour=23))
        end_sleep = datetime.datetime.combine(time.date(), datetime.time(hour=7))
        return time < end_sleep or time > start_sleep


    def special_time(self, time_from, time_to):
        """
        result = datetime.timedelta()
        while time_from < time_to:
            if self.is_sleeping_time(time_from):
                result += datetime.timedelta(hours=1)
            time_from += datetime.timedelta(hours=1)
        return result
        """
        span = timespans.TimeSpanSet(timespans = [])

        for t in self.tasks:
            if t.periodics:
                span += t.generate_timespanset(time_from, time_to)
        return span.length()

    def check(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()

        limited_tasks = [task for task in self.tasks if task.upper_limit is not None and not task.periodics]
        unbound_tasks = [task for task in self.tasks if task.upper_limit is None and task.length is not None and not task.periodics]
        limited_tasks.sort(key = lambda task : task.upper_limit)

        budget = datetime.timedelta()
        now = date_from
        for task in limited_tasks:
            status = "nominal"
            if task.upper_limit<date_from:
                status = "OVERDUE"
            else:
                budget += task.upper_limit - now
                budget -= self.special_time(now, task.upper_limit)
                budget -= datetime.timedelta(hours=task.length)
                if budget < datetime.timedelta():
                    status = "FUCKUP"
                now = task.upper_limit
            if status != 'nominal':
                print (status, task)
        assigned_time = sum([datetime.timedelta(hours = task.length) for task in limited_tasks], datetime.timedelta())
        print (assigned_time, " time scheduled")
        print (budget, " unscheduled worktime left")
        unbound_time = sum([datetime.timedelta(hours = task.length) for task in unbound_tasks], datetime.timedelta())
        print ("All other tasks are", unbound_time)
        left = (budget - unbound_time).total_seconds()/60.0/60
        print (abs(left), "h of unassigned time" if left > 0 else "h shortage")

        if unbound_time > budget:
            print ("You're short of time. Either limit some unbound tasks, or postpone some of limited")
        else:
            print ("NOMINAL")

    def scheduled(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()
        limited_tasks = [task for task in self.tasks if task.upper_limit is not None]
        limited_tasks.sort(key = lambda task : task.upper_limit)
        for task in limited_tasks:
            print (task)
            
def load_all():
    taskpool = TaskList()
    lists_dir = get_dir()
    for filename in os.listdir(lists_dir):
        if filename.endswith(".todo"):
            taskpool.load_from_file(lists_dir+filename)
    return taskpool

if __name__== "__main__":
     print (TaskList().special_time(datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days = 1)).seconds/3600)
     
     print (looks_like_length('100ч'))
     print ("100ч"[:-1])
     print (get_length('100ч'))
