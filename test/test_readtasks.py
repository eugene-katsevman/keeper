from unittest import TestCase
from keeper.tasks import TaskList, Task
import io

import pytest

def test_simple():
    data = io.StringIO("""
task1
 task2
  task3
   task4
  task5
  task51

 task6
  task7

task8
    """)
    tasklist = TaskList(filename='test/somefile', stream=data)
    task1 = tasklist.find_task('task1')
    assert task1.children
    assert len(task1.children) == 2

    task2 = tasklist.find_task('task2')
    assert len(task2.children) == 3


@pytest.mark.parametrize('spec,expected_todo', [
    ("""
task1
 task2 [done]
  task3
   task4
  task5
  task51
 task6
  task7 [done]

task8
        """, 'task6'),

    ("""
    task1
     task2 [done]
      task3
       task4
      task5
      task51
     task6
      task7
    
    task8
        """, 'task7'),
])
def test_find_first(spec, expected_todo):
    data = io.StringIO(spec)
    tasklist = TaskList(filename='test/somefile', stream=data)
    task6 = tasklist.find_task(expected_todo)
    todo = tasklist.find_first_to_do()
    assert task6 == todo

