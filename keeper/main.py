#!env python

import click
import os
import random
import operator
import subprocess

from keeper import settings, utils
from keeper import common


DURATION_GETTER = operator.attrgetter('duration_left')


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


@main.command(help='open specified .todo files using'
                   ' editor set in .keeperrc. ')
@click.argument('filenames', nargs=-1)
def edit(filenames):
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


@main.command(help='Quick check current scheduled tasks')
def check():
    common.load_all().check()


@main.command(help='Show scheduled tasks')
def scheduled():
    common.load_all().scheduled()


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
    taskpool = common.load_all()
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
    for task in common.load_all().today():
        click.echo(task)


@main.command(help='What to do now')
def what():
    click.echo(common.load_all().find_first_to_do())


@main.command(help='Enter workmode')
def workmode():
    taskpool = common.load_all()
    last_task = None
    while True:
        current = taskpool.find_first_to_do(last_task)
        if not current:
            break
        click.echo(current)
        click.echo('[W]tf?/[D]one/[S]plit/[Q]uit/[L]ater/Add [B]efore')
        decision = click.getchar()
        decision = {'й': 'q',
                    'в': 'd',
                    'ы': 's',
                    'д': 'l',
                    'ц': 'w',
                    'и': 'b'}.get(decision, decision)
        if decision == 'q':
            exit()
        if decision not in ['d', 's', 'l', 'w', 'b']:
            click.echo('Unknown command')
            continue
        if decision == 'd':
            common.mark_done(current)
        elif decision == 'l':
            last_task = current
        elif decision == 'w':
            c = current
            while c.parent:
                print("Because of", c.parent)
                c = c.parent
        elif decision == 'b':
            click.echo('Print new task, finish with empty line:')
            line = input()
            if line:
                common.prepend(current, line)

        elif decision == 's':
            click.echo('Print new task, finish with empty line:')
            while True:
                line = input()
                if line:
                    common.add_child(current, line)
                else:
                    break
    print("Congrats! You've finished!")


@main.command(help='Show ten random tasks', name='random')
@click.option('--no-total', is_flag=True, help='do not output total worktime')
def random_tasks(no_total):
    task_list = [task for task in common.load_all().tasks
                 if not task.periodics and not task.upper_limit]
    sample = random.sample(task_list, 10)
    for task in sample:
        click.echo(task)
    if not no_total:
        click.echo("Total: {}h of worktime".format(total_duration(sample)))


@main.command(help='List all available topics')
def show_topics():
    taskpool = common.load_all()
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


if __name__ == '__main__':
    main()
