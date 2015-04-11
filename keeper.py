#!/usr/bin/python
import tasks
import sys



taskpool = tasks.load_all();

taskpool.tasks.sort(key = lambda task : task.length)

for task in taskpool.tasks:
    print task
