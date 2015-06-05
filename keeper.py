#!/usr/bin/python
# -*- coding:utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import tasks
import sys
import settings
import argparse
import random
from settings import *
from datetime import datetime

taskpool = tasks.load_all()

def check(arg):    
    taskpool.check()

def scheduled(arg):
    taskpool.scheduled()

def list_topic(arg):
    task_list = [task for task in taskpool.tasks if not args.topic or set(task.topics).intersection(set(arg.topic))]
    if arg.topic:
        if set(arg.topic).intersection(set(IGNORED_SECTIONS)):
            print "in ignored"
            task_list += [task for task in taskpool.special_tasks if not args.topic or set(task.topics).intersection(set(arg.topic))]
    if args.unscheduled:
        task_list = [task for task in task_list if not task.upper_limit]
    for task in task_list:
        print task
    if not args.no_total:
        print "Total: ", len(task_list), "task(s), ", sum([task.length for task in task_list if task.length]), "h of worktime"

def today(arg):
    for task in taskpool.today():
        print task

def test(arg):
    task_list = [task for task in taskpool.tasks if task.periodics]
    for task in task_list:
        print task
        print task.generate_timespanset(datetime(2015, 5, 1), datetime(2015, 5, 9))

def random_tasks(arg):
    task_list = [task for task in taskpool.tasks if not task.periodics and not task.upper_limit]
    
    sample = random.sample(task_list, 10)
    for task in sample:
        print task
    if not args.no_total:
        print "Total: ", sum([task.length for task in sample if task.length]), "h of worktime"
        

parser = argparse.ArgumentParser(description='console timekeeper')
subparsers = parser.add_subparsers()
parser_check = subparsers.add_parser('check', help='Quick check current scheduled tasks')
parser_check.set_defaults(func=check)

parser_scheduled = subparsers.add_parser('scheduled', help='Show scheduled tasks')
parser_scheduled.set_defaults(func=scheduled)

parser_list = subparsers.add_parser('list', help='List all tasks')
parser_list.add_argument("topic", nargs="*")
parser_list.add_argument("--no-total", action="store_true", help = "do not count total work hours")
parser_list.add_argument("--unscheduled", action="store_true", help = "show unscheduled tasks only")
parser_list.set_defaults(func=list_topic, topic = None)


parser_today = subparsers.add_parser('today', help='Lists tasks for today')
parser_today.set_defaults(func=today)

parser_test = subparsers.add_parser('test', help='Testy test')
parser_test.set_defaults(func=test)

parser_random = subparsers.add_parser('random', help='Show ten random tasks')
parser_random.add_argument("--no-total", action="store_true", help = "do not count total work hours")

parser_random.set_defaults(func=random_tasks)

if (len(sys.argv) < 2):
    args = parser.parse_args(['check'])
elif sys.argv[1] == "current":
    args = parser.parse_args(['list', 'current'])
else:
    args = parser.parse_args()
    

args.func(args)
