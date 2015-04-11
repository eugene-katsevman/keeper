#!/usr/bin/python
import tasks
import sys
import settings


taskpool = tasks.load_all();

taskpool.tasks.sort(key = lambda task : task.length)

for task in taskpool.tasks:
    print task
    
print "total time:", sum([task.length for task in taskpool.tasks if task.length is not None])
