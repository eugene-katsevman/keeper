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
import platform
import os

WINDOWS = platform.system() == "Windows"

taskpool = tasks.load_all()

def check(arg):    
    taskpool.check()

def scheduled(arg):
    taskpool.scheduled()

def list_topic(arg):
    if args.topic and WINDOWS:
        args.topic = [topic.decode('windows-1251') for topic in args.topic]



    if not args.topic:
        task_list = taskpool.tasks
    else:
        task_list = []
        topic_list_or = [set(topic.split('.')) for topic in arg.topic]
        for topic_list_and in topic_list_or:
            if topic_list_and.intersection(IGNORED_SECTIONS):
                src_list = taskpool.special_tasks
            else:
                src_list = taskpool.tasks
            for task in src_list:
                if set(task.topics).issuperset(topic_list_and):
                    task_list.append(task)

    if args.unscheduled:
        task_list = [task for task in task_list if not task.upper_limit]
    if args.sort:
        task_list.sort(key = lambda task : task.length)
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


def edit(arg):
    if args.filenames:
        os.system("gedit "+" ".join(["~/work/keeper/lists/"+fn + ".todo" for fn in args.filenames]))
    else:
        os.system("todo")


def show_topics(arg):
    topics = list(set.union(*[set(task.topics) for task in taskpool.tasks + taskpool.special_tasks]))
    topics.sort()
    for topic in topics:
        print topic

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
parser_list.add_argument("--sort", action="store_true", help = "sort output by length")
parser_list.set_defaults(func=list_topic, topic = None)


parser_today = subparsers.add_parser('today', help='Lists tasks for today')
parser_today.set_defaults(func=today)

parser_test = subparsers.add_parser('test', help='Testy test')
parser_test.set_defaults(func=test)

parser_random = subparsers.add_parser('random', help='Show ten random tasks')
parser_random.add_argument("--no-total", action="store_true", help = "do not count total work hours")

parser_random.set_defaults(func=random_tasks)

parser_edit = subparsers.add_parser('edit', help='start default system editor for all todo files')
parser_edit.add_argument("filenames", nargs="*")
parser_edit.set_defaults(func=edit)


parser_topics = subparsers.add_parser('topics', help='show topic list and some stats')
parser_topics.set_defaults(func=show_topics)

if (len(sys.argv) < 2):
    args = parser.parse_args(['check'])
elif sys.argv[1] == "current":
    args = parser.parse_args(['list', 'current'])
else:
    args = parser.parse_args()
    

args.func(args)
