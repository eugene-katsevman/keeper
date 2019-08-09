import io

from keeper.source import Attributes
from keeper.source import TaskLine
from keeper.source import TaskSource

def test_attributes():
    attributes = Attributes(10, 'hello,    there   ,    + 10')
    assert len(attributes.attrs) == 3
    assert attributes.attrs[0].value == 'hello'
    assert attributes.attrs[1].value == 'there'
    assert attributes.attrs[2].value == '+ 10'
    assert attributes.attrs[2].location == 29

    assert attributes.attrs[0].value == attributes[0].value


def test_source():
    data = io.StringIO(
        '''
        task1
        task2[done]  #something
          task3[a1, a2, a3    ,   a4]
        '''
    )
    source = TaskSource(filename='imaginary', stream=data)

    assert len(source.lines) == 5
    assert len(source.tasks) == 2
    assert source.lines[2].has_attr('done')

