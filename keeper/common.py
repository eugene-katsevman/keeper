from keeper.source import get_level, TaskLine, extract_attributes
from keeper.task import Task


def prepend(task: Task, line: str):
    appended_level = get_level(task.source.line)
    line = ' ' * appended_level + line
    source_line = TaskLine(line)
    attributes = extract_attributes(line)
    attributes['parent'] = task.parent
    attributes['source'] = source_line
    new_task = Task(**attributes)
    task.source.source.add_task(new_task, first=True)
    append_before = task.source.source.lines.index(task.source)
    task.source.source.insert_before(source_line, append_before)
    task.source.save()


def mark_done(current: Task):
    current.source.add_attr('done')
    current.source.save()
    current.topics.append('done')


def add_child(current: Task, line: str):
    last_task = current
    while last_task.children:
        last_task = last_task.children[-1]
    append_after = current.source.source.lines.index(last_task.source)

    appended_level = get_level(current.source.line) + 1
    line = ' ' * appended_level + line
    source_line = TaskLine(line)
    attributes = extract_attributes(line)
    attributes['parent'] = current
    attributes['source'] = source_line
    new_task = Task(**attributes)
    current.source.source.add_task(new_task)
    current.source.source.insert_after(source_line, append_after)
    append_after = source_line
    current.source.save()
