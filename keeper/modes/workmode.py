import click

from keeper.source import TaskLine
from keeper.source import extract_attributes
from keeper.source import get_level
from keeper.task import Task
from keeper.tasklist import TaskList


def prepend(task: Task, line: str) -> None:
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


def mark_done(current):
    current.source.add_attr('done')
    current.source.save()
    current.topics.append('done')


def add_child(current, line):
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
    current.source.save()


def workmode(taskpool: TaskList):

    last_task = None
    while True:
        current = taskpool.find_first_to_do(last_task)
        if not current:
            break
        click.echo(current)
        click.echo('[W]tf?/[D]one/[S]plit/[Q]uit/[L]ater/Add [B]efore')
        decision = click.getchar()
        decision = {
            'й': 'q',
            'в': 'd',
            'ы': 's',
            'д': 'l',
            'ц': 'w',
            'и': 'b'
        }.get(decision, decision)
        if decision == 'q':
            exit()
        if decision not in ['d', 's', 'l', 'w', 'b']:
            click.echo('Unknown command')
            continue
        if decision == 'd':
            mark_done(current)
        elif decision == 'l':
            last_task = current
        elif decision == 'w':
            c = current
            while c.parent:
                click.echo("Because of", c.parent)
                c = c.parent
        elif decision == 'b':
            click.echo('print new task, finish with empty line:')
            line = input()
            if line:
                prepend(current, line)

        elif decision == 's':
            click.echo('print new task, finish with empty line:')
            while True:
                line = input()
                if line:
                    add_child(current, line)
                else:
                    break
    click.echo("Congrats! You've finished!")
