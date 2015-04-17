#!/usr/bin/python
# -*- coding:utf8 -*-
# PYTHON_ARGCOMPLETE_OK
import tasks
import sys
import settings
import argparse
from datetime import datetime



taskpool = tasks.load_all()


parser = argparse.ArgumentParser(description='console timekeeper')
subparsers = parser.add_subparsers()
parser_check = subparsers.add_parser('check', help='Quick check current scheduled tasks')
parser_check.set_defaults(func=taskpool.check)

parser_scheduled = subparsers.add_parser('scheduled', help='Show scheduled tasks')
parser_scheduled.set_defaults(func=taskpool.scheduled)

#parser_append.add_argument('username', help='Name of user')
#parser_append.add_argument('age', help='Age of user')


args =  parser.parse_args()


args.func(args)


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
