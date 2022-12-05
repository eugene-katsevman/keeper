import random

from keeper.tasklist import TaskList


def sortmode(taskpool: TaskList):
    a = random.choice(taskpool.tasks)
    b = random.choice(taskpool.tasks)
    print(a)
    print(b)
