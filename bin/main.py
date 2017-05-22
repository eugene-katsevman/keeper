#!/usr/bin/python3
# -*- coding:utf-8 -*-


import os
import sys
import argparse
import random
from datetime import datetime
import platform
import errno

keeper_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, keeper_dir)
from keeper import tasks, settings


WINDOWS = platform.system() == "Windows"

lists_dir = tasks.get_dir()

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

mkdir_p(lists_dir)
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
            if topic_list_and.intersection(settings.IGNORED_SECTIONS):
                src_list = taskpool.special_tasks
            else:
                src_list = taskpool.tasks
            for task in src_list:
                if set(task.topics).issuperset(topic_list_and):
                    task_list.append(task)

    task_list = [task for task in task_list if not task.periodics]

    if args.unscheduled:
        task_list = [task for task in task_list if not task.upper_limit]
    if args.sort:
        task_list.sort(key = lambda task : task.length)
        
    if args.australian:
        for t in task_list:
         t.name = t.name.replace("bear", "kangaroo")
        
    for task in task_list:
        print (task)
        if args.set_attr:
            task.add_attr_back(args.set_attr)
    if not args.no_total:
        print ("Total: ", len(task_list), "task(s), ", sum([task.length for task in task_list if task.length]), "h of worktime", \
            sum([task.cost for task in task_list if task.cost]), "rubles gain")


def today(arg):
    for task in taskpool.today():
        print (task)

def test(arg):
    t = taskpool.tasks[0].taskline
    t.remove_attr_by_value('don')
    t.remove_attr_by_value('alala')
    t.remove_attr_by_value('attr2')
    t.save()

def work(arg):
    import cmd
    class WorkCmd(cmd.Cmd):
        def __init__(self):
            cmd.Cmd.__init__(self)
            self.prompt = '>'

        def do_exit(self, arg):
            """
            Exit
            """
            print ("Have a nice day!")
            return True
        def show_tasks(self):
            for i, task in enumerate(taskpool.tasks):
                print ("{}) {}".format(i, str(task)))
        def do_current(self, arg):
            self.show_tasks()

    mycmd = WorkCmd()
    mycmd.cmdloop("You have entered keeper's interactive mode")


def random_tasks(arg):
    task_list = [task for task in taskpool.tasks if not task.periodics and not task.upper_limit]
    
    sample = random.sample(task_list, 10)
    for task in sample:
        print (task)
    if not args.no_total:
        print ("Total: ", sum([task.length for task in sample if task.length]), "h of worktime")


def edit(arg):
    if args.filenames:
        os.system("xed "+" ".join([tasks.get_dir()+fn + ".todo" for fn in args.filenames]))
    else:
        os.system("xed "+tasks.get_dir()+"*.todo")


def show_topics(arg):
    topics = list(set.union(*[set(task.topics) for task in taskpool.tasks + taskpool.special_tasks]))
    topics.sort()
    for topic in topics:
        print (topic)

def done(arg):
    lists_dir = tasks.get_dir()
    for filename in arg.files:
        _from, _to = lists_dir+filename+".todo", lists_dir+filename+".done"
        print ("moving {} to {}".format(_from, _to))
        os.rename(_from, _to)

def undo(arg):
    lists_dir = tasks.get_dir()
    for filename in arg.files:
        _from, _to = lists_dir+filename+".done", lists_dir+filename+".todo"
        print ("moving {} to {}".format(_from, _to))
        os.rename(_from, _to)

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
parser_list.add_argument("--australian", action="store_true", help = "accomodate for Australian nature")
parser_list.add_argument("--set_attr", help = "set custom attr")
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

parser_done = subparsers.add_parser('done', help='mark file as done')
parser_done.add_argument("files", nargs="+", help="file names to be marked as done")
parser_done.set_defaults(func=done)

parser_undo = subparsers.add_parser('undo', help='revert done file to todo')
parser_undo.add_argument("files", nargs="+", help="done file names to be reverted")
parser_undo.set_defaults(func=undo)

parser_work = subparsers.add_parser('work', help='simple interactive mode')
parser_work.set_defaults(func=work)

if (len(sys.argv) < 2):
    args = parser.parse_args(['check'])
elif sys.argv[1] == "current":
    args = parser.parse_args(['list', 'current'])
else:
    args = parser.parse_args()
    

args.func(args)
