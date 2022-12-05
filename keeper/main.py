#!env python
import typing

import click
import os
import random
import operator
import subprocess

from keeper import modes
from keeper import settings, utils
from keeper.settings import APP_DIRECTORY
from keeper.source import TaskSource
from keeper.tasklist import TaskList
from keeper.utils import td_to_hours

DURATION_GETTER = operator.attrgetter('duration_left')


def load_all() -> TaskList:
    task_pool = TaskList()
    lists_dir = APP_DIRECTORY
    for filename in os.listdir(lists_dir):
        if filename.endswith('.todo'):
            real_filename = os.path.join(lists_dir, filename)
            source = TaskSource(filename=real_filename)
            task_pool.add_source(source)
    return task_pool


def find_first_editor():
    """
    :raises: RuntimeError
    :rtype: str
    :return: first installed editor from the `settings.POSSIBLE_EDITORS` list
    """
    for editor in settings.POSSIBLE_EDITORS:
        if 0 == subprocess.call(['which', editor]):
            return editor
    raise RuntimeError('No editor found. Please configure one in .keeperrc')


@click.group(help='Console timekeeper', invoke_without_command=True)
@click.pass_context
def main(ctx):
    """
    Entrypoint
    """
    # check and create app directory if necessary
    utils.mkdir_p(settings.APP_DIRECTORY)
    if ctx.invoked_subcommand is None:
        ctx.invoke(check)


def _run_edit(filenames: typing.List[str]):
    """
        open files from filenames using editor from settings or
        found by `find_first_editor`

        :type filenames: argparse.Namespace
        :param filenames: filenames to open
        """
    if not filenames:
        # check if ANY file exists within dir
        w = os.walk(settings.APP_DIRECTORY)
        path, attrs, files = next(w)
        exists = any(file.endswith('.todo') for file in files)
        filenames = ['*'] if exists else ['main']

    full_filenames = [fn if fn.endswith('.todo')
                      else '%s.todo' % fn for fn in filenames]

    if not settings.EDITOR or settings.EDITOR == 'auto':
        editor = find_first_editor()
    else:
        editor = settings.EDITOR

    files_to_open = [os.path.join(settings.APP_DIRECTORY, fn)
                     for fn in full_filenames]

    command_str = "{editor} {files_to_open_str}".format(
        editor=editor,
        files_to_open_str=" ".join(files_to_open)
    )

    os.system(command_str)


@main.command(help='open specified .todo files using'
                   ' editor set in .keeperrc. ')
@click.argument('filenames', nargs=-1)
def edit(filenames):
    _run_edit(filenames)


@main.command(help='Quick check current scheduled tasks')
def check():
    result = load_all().check(date_from=None)
    print('Assigned time (how long limited tasks will take):'.ljust(50),
          td_to_hours(result.assigned_time))
    print('Balance (time total balance for limited tasks):'.ljust(50),
          td_to_hours(result.balance))
    print('Unbound time (how long free tasks will take):'.ljust(50),
          td_to_hours(result.unbound_time))
    # (Can we do both limited and free tasks?)
    print('Free time left till latest limited task:'.ljust(50),
          td_to_hours(result.left))
    if result.left.total_seconds() < 0:
        print('You\'re short of time. Either limit some unbound tasks,'
              ' or postpone some of limited',)
    print()
    if not result.overdue and not result.risky:
        print('We\'re good')
    else:
        for task in result.overdue:
            print('OVERDUE', task)
        for task in result.risky:
            print('RISKY', task)


@main.command(help='Show scheduled tasks')
def scheduled():
    limited_tasks = load_all().scheduled()
    for task in limited_tasks:
        print(task)


def total_duration(task_list):
    durations = filter(None, map(DURATION_GETTER, task_list))
    return sum(durations)


@main.command(help='List tasks', name='list')
@click.argument("topics", nargs=-1)
@click.option('--no-total', is_flag=True, help='Do not count total'
              ' work hours')
@click.option('--unscheduled', is_flag=True,
              help='Show unscheduled tasks only')
@click.option('--sort', is_flag=True, help='Sort output by duration_left')
def list_topic(topics, no_total, unscheduled, sort):
    taskpool = load_all()
    if not topics:
        task_list = taskpool.tasks
    else:
        task_list = []
        topic_list_or = [set(topic.split('.')) for topic in topics]
        for topic_list_and in topic_list_or:
            if topic_list_and.intersection(settings.IGNORED_SECTIONS):
                src_list = taskpool.special_tasks
            else:
                src_list = taskpool.tasks
            for task in src_list:
                if set(task.topics).issuperset(topic_list_and):
                    task_list.append(task)

    task_list = [task for task in task_list if not task.periodics]

    if unscheduled:
        task_list = [task for task in task_list if not task.upper_limit]
    if sort:
        task_list.sort(key=DURATION_GETTER)

    for task in task_list:
        click.echo(task)
    if not no_total:
        total = total_duration(task_list)
        click.echo("Total: {} tasks(s), {}h of worktim".format(len(task_list),
                                                               total))


@main.command(help='Lists tasks for today')
def today():
    for task in load_all().today():
        click.echo(task)


@main.command(help='What to do now')
def what():
    click.echo(load_all().find_first_to_do())


@main.command(help='Enter workmode')
def workmode():
    modes.workmode(load_all())


@main.command(help='Enter sortmode')
def sortmode():
    modes.sortmode(load_all())


@main.command(help='Show ten random tasks', name='random')
@click.option('--no-total', is_flag=True, help='do not output total worktime')
def random_tasks(no_total):
    task_list = [task for task in load_all().tasks
                 if not task.periodics and not task.upper_limit]
    sample = random.sample(task_list, 10)
    for task in sample:
        click.echo(task)
    if not no_total:
        click.echo("Total: {}h of worktime".format(total_duration(sample)))


@main.command(help='List all available topics')
def show_topics():
    taskpool = load_all()
    all_tasks = taskpool.tasks + taskpool.special_tasks
    topics = list(set.union(*[set(task.topics) for task in all_tasks]))
    topics.sort()
    for topic in topics:
        click.echo(topic)


@main.command(help='Rename [filename].todo to [filename].done\n')
@click.argument('filenames', nargs=-1)
def done(filenames):
    lists_dir = settings.APP_DIRECTORY
    for filename in filenames:
        _from = os.path.join(lists_dir,
                             filename + ".todo")
        _to = os.path.join(lists_dir, filename + ".done")
        click.echo("moving {} to {}".format(_from, _to))
        os.rename(_from, _to)


@main.command(help='Rename [filename].done to [filename].todo\n')
@click.argument('filenames', nargs=-1)
def undo(filenames):
    lists_dir = settings.APP_DIRECTORY
    for filename in filenames:
        _from = os.path.join(lists_dir, filename + ".done")
        _to = os.path.join(lists_dir, filename + ".todo")
        click.echo("moving {} to {}".format(_from, _to))
        os.rename(_from, _to)


@main.command(help="Open inbox.todo for editing")
def inbox():
    _run_edit(['inbox'])


if __name__ == '__main__':
    main()


