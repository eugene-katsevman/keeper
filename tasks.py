# -*- coding:utf-8 -*-
import os
import re
import datetime
import os.path
from settings import *


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

def looks_like_till_datetime(s):
    return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_till_date(s):
    return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d', s)

def looks_like_length(s):
    return [] != re.findall('\d+[hmчм]|\?[hmчм]', s)

class Task:
    def __init__(self, name = "", length = 1, topic = None, topics = [], at = None, till = None):
        self.name = name
        self.length = length
        self.topic = topic
        
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
    
    def __str__(self):

        return "{} {} [{}]".format(self.topic, self.name, self.planned_time_to_str())

        
class TaskList:
    def __init__(self, filename = None):
        self.tasks = []
        self.special_tasks = []
        if filename:
            self.load_from_file(filename)
        
    def load_from_file(self, filename):
        current_section = None
        for line in open(filename).readlines():        
            line = line.rstrip()
            if line:
                if line.strip().startswith('//') or line.strip().startswith('#'):
                    pass
                elif line.endswith(':'):
                    current_section = line.strip()[:-1]
                else:
                    if not line.startswith(' '):
                        current_section = None
                    attributes = self.extract_attributes(line)
                    attributes['topic'] = current_section
                    attributes['topics'] = [os.path.basename(filename).split('.')[0]]
                    if current_section:
                        attributes['topics'].append(current_section)

                    if current_section not in IGNORED_SECTIONS:
                        self.tasks.append(Task(**attributes))
                    else:
                        self.special_tasks.append(Task(**attributes))

    @staticmethod
    def extract_attributes(line):
        try:
            result = dict()
            result['name'] = line.strip()
            times = re.findall('\d+[hm]|\?[hm]', line)
            if times:
                time = times[0]
                result['length'] = get_length(time)
            attribute_line = re.findall('\[(.*)\]', line)
            if attribute_line:
                attributes = [attr.strip() for attr in attribute_line[0].split(',')]
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
            return result                        
        except Exception as e:
            raise Exception("error while parsing {} of topic {}".format(line, topic))

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
        result = datetime.timedelta()
        while time_from < time_to:
            if self.is_sleeping_time(time_from):
                result += datetime.timedelta(hours=1)
            time_from += datetime.timedelta(hours=1)
        return result

    def check(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()

        limited_tasks = [task for task in self.tasks if task.upper_limit is not None]
        unbound_tasks = [task for task in self.tasks if task.upper_limit is None and task.length is not None]
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
            if status != 'nominal': print status, task
        assigned_time = sum([datetime.timedelta(hours = task.length) for task in limited_tasks], datetime.timedelta())
        print assigned_time, " time scheduled"
        print budget, " unscheduled worktime left"
        unbound_time = sum([datetime.timedelta(hours = task.length) for task in unbound_tasks], datetime.timedelta())
        print "All other tasks are", unbound_time
        if unbound_time > budget:
            print "You're short of time. Either limit some unbound tasks, or postpone some of limited"
        else:
            print budget - unbound_time, " of unassigned time"
            print "NOMINAL"

    def scheduled(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()
        limited_tasks = [task for task in self.tasks if task.upper_limit is not None]
        limited_tasks.sort(key = lambda task : task.upper_limit)
        for task in limited_tasks:
            print task
            
def load_all():
    taskpool = TaskList()
    lists_dir = os.path.dirname(__file__)+"/lists/"
    for filename in os.listdir(lists_dir):
        taskpool.load_from_file(lists_dir+filename)
    return taskpool

if __name__== "__main__":
     print TaskList().special_time(datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days = 1)).seconds/3600
     
     print looks_like_length('100ч')
     print "100ч"[:-1]
     print get_length('100ч')
