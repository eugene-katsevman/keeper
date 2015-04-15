# -*- coding:utf8 -*-
import sys
import os.path
import os
import re
import datetime
import os.path

class Task:
    def __init__(self, name = "", length = 1, topic = None, at = None, till = None):
        self.name = name
        self.length = length
        self.topic = topic
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
        if filename:
            self.load_from_file(filename)
        
    def load_from_file(self, filename):
        current_section = None
        for line in open(filename).readlines():        
            line =  line.rstrip()
            if line:
                if line.endswith(':'):
                    current_section = line.strip()[:-1]                    
                else:
                    if not line.startswith(' '):
                        current_section = None
                    if current_section != 'done':
                        attributes = self.extract_attributes(current_section, line)
                        
                        self.tasks.append(Task(**attributes))    

                            
    def extract_attributes(self, topic, line):
        def get_length(s):
            if '?' in time:
                return None
            elif time.endswith('h'):            
                return int(time[:-1])   
            elif time.endswith('m'):
                return float(time[:-1]) / 60
                
        def looks_like_date(s):
            return [] != re.findall('^\d\d?\.\d\d?\.\d\d\d\d', s)

        def looks_like_till_date(s):
            return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d', s)

        def looks_like_length(s):
            return [] != re.findall('\d+[hm]|\?[hm]', s)            
            
        result = dict()
        result['topic'] = topic
        result['name'] = line.strip()
        times = re.findall('\d+[hm]|\?[hm]', line)
        if times:
            time = times[0]
            result['length'] = get_length(time)
        attribute_line = re.findall('\[(.*)\]', line)
        if attribute_line:
            attributes = [attr.strip() for attr in attribute_line[0].split(',')]
            for attr in attributes:
                if looks_like_date(attr):
                    format = '%d.%m.%Y'
                    date_object = datetime.datetime.strptime(attr, format)
                    result['at'] = date_object
                    
                elif looks_like_length(attr):
                    result['length'] = get_length(attr)              
                elif looks_like_till_date(attr):
                    format = '%d.%m.%Y'
                    date_object = datetime.datetime.strptime(attr[1:], format)
                    result['till'] = date_object

                    
        return result
        
    def today(self):
        return [task for task in self.tasks if task.topic in ["сегодня", "today"]]
        
    def strict_at(self, date):
        return [task for task in self.tasks if task.at == date]
    
    def till(self, date):
        return [task for task in self.tasks if task.till != None and task.till<=date] + self.strict_at(date)

    def estimate(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()


        limited_tasks = [task for task in self.tasks if task.upper_limit is not None]
        limited_tasks.sort(key = lambda task : task.upper_limit)
        overdue = set()
        fuckups = set()
        now = date_from
        budget = datetime.timedelta()
        for task in limited_tasks:
            status = "nominal"
            if task.upper_limit<date_from:
                status = "overdue"
            else:
                budget += task.upper_limit - now
                budget -= datetime.timedelta(hours=task.length)
                if budget < datetime.timedelta():
                    status = "possible fuckup"
                now = task.upper_limit
            print status, task


            
def load_all():
    taskpool = TaskList()
    lists_dir = os.path.dirname(__file__)+"/lists/"
    for filename in os.listdir(lists_dir):
        taskpool.load_from_file(lists_dir+filename)
    return taskpool
