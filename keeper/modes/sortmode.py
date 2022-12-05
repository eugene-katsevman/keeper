import random

from keeper.taskpool import TaskPool


def sortmode(taskpool: TaskPool):
    a = random.choice(taskpool.tasks)
    b = random.choice(taskpool.tasks)
    print(a)
    print(b)
