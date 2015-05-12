#!/usr/bin/python
# -*- coding:utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import tasks
import sys
import settings
import argparse
from datetime import datetime

taskpool = tasks.load_all()

def check(arg):    
    taskpool.check()

def scheduled(arg):
    taskpool.scheduled()

def list_topic(arg):
    tasklist = [task for task in taskpool.tasks if not args.topic or set(task.topics).intersection(set(arg.topic))]
    for task in tasklist:
        print task
    if not args.no_total:
        print "Total: ", sum([task.length for task in tasklist if task.length])

def today(arg):
    for task in taskpool.today():
        print task
    
parser = argparse.ArgumentParser(description='console timekeeper')
subparsers = parser.add_subparsers()
parser_check = subparsers.add_parser('check', help='Quick check current scheduled tasks')
parser_check.set_defaults(func=check)

parser_scheduled = subparsers.add_parser('scheduled', help='Show scheduled tasks')
parser_scheduled.set_defaults(func=scheduled)

parser_list = subparsers.add_parser('list', help='List all tasks')
parser_list.add_argument("topic", nargs="*")
parser_list.add_argument("--no-total", action="store_true")
parser_list.set_defaults(func=list_topic, topic = None)


parser_today = subparsers.add_parser('today', help='Lists tasks for today')
parser_today.set_defaults(func=today)



#parser_append.add_argument('username', help='Name of user')
#parser_append.add_argument('age', help='Age of user')

if (len(sys.argv) < 2):
    args = parser.parse_args(['check'])
else:
    args = parser.parse_args()
    

args.func(args)
