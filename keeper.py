#!/usr/bin/python
import tasks
import sys
import settings
import argparse
from datetime import datetime


taskpool = tasks.load_all();

"""
taskpool.tasks.sort(key = lambda task : task.length)

for task in taskpool.tasks:
    print task
    
total_time = sum([task.length for task in taskpool.tasks if task.length is not None])    
print "total time:", total_time
print "days:", total_time / 10
print "today:"
for task in taskpool.today():
    print task
    
print "14.04.2015"
for task in taskpool.strict_at(datetime(2015, 4, 14)):
    print task

print "<16.04.2015"
till_tasks = taskpool.till(datetime(2015, 4, 16)) 
for task in till_tasks:
    print task

print sum([task.length for task in till_tasks if task.length is not None])
"""
taskpool.estimate()