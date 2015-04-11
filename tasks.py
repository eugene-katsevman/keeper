import sys
import os.path
import os
import re

class Task:
    def __init__(self, name = "", length = 1, topic = None):
        self.name = name
        self.length = length
        self.topic = topic
        
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
                    if current_section != 'done':
                        attributes = self.extract_attributes(current_section, line)
                        
                        self.tasks.append(Task(**attributes))    
                        
    def extract_attributes(self, topic, line):
        result = dict()
        result['topic'] = topic
        result['name'] = line.strip()
        times = re.findall('\d+[hm]|\?[hm]', line)
        if times:
            time = times[0]
            if '?' in time:
                result['length'] = None
            elif time.endswith('h'):            
                result['length'] = int(time[:-1])   
            elif time.endswith('m'):
                result['length'] = float(time[:-1]) / 60
        return result    

def load_all():
    taskpool = TaskList()
    for filename in os.listdir('./lists'):
        taskpool.load_from_file('./lists/'+filename)
    return taskpool
