import random

from keeper.taskpool import TaskPool


# TODO: unfinished. Sortmode is not implemented yet; it only prints two random tasks.
def sortmode(taskpool: TaskPool):
    a = random.choice(taskpool.tasks)
    b = random.choice(taskpool.tasks)
    print(a)
    print(b)
