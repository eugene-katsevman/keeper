#!env python


import os
import sys
import argparse
import random
import operator
import subprocess

from keeper import tasks, settings


DURATION_GETTER = operator.attrgetter('duration_left')


def get_taskpool():
    lists_dir = tasks.get_dir()
    tasks.mkdir_p(lists_dir)
    taskpool = tasks.load_all()
    return taskpool


def check(args):
    get_taskpool().check()


def scheduled(args):
    get_taskpool().scheduled()


def total_duration(task_list):
    durations = filter(None, map(DURATION_GETTER, task_list))
    return sum(durations)


def list_topic(args):
    taskpool = get_taskpool()
    if not args.topic:
        task_list = taskpool.tasks
    else:
        task_list = []
        topic_list_or = [set(topic.split('.')) for topic in args.topic]
        for topic_list_and in topic_list_or:
            if topic_list_and.intersection(settings.IGNORED_SECTIONS):
                src_list = taskpool.special_tasks
            else:
                src_list = taskpool.tasks
            for task in src_list:
                if set(task.topics).issuperset(topic_list_and):
                    task_list.append(task)

    task_list = [task for task in task_list if not task.periodics]

    if args.unscheduled:
        task_list = [task for task in task_list if not task.upper_limit]
    if args.sort:
        task_list.sort(key=DURATION_GETTER)

    for task in task_list:
        print(task)
        if args.set_attr:
            task.add_attr_back(args.set_attr)
    if not args.no_total:
        total = total_duration(task_list)
        print("Total: ", len(task_list), "task(s), ", total, "h of worktime")


def today(args):
    for task in get_taskpool().today():
        print(task)


def random_tasks(args):
    task_list = [task for task in get_taskpool().tasks
                 if not task.periodics and not task.upper_limit]

    sample = random.sample(task_list, 10)
    for task in sample:
        print(task)
    if not args.no_total:
        print("Total: ", total_duration(sample), "h of worktime")


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



def edit(args):
    filenames = args.filenames or '*'
    full_filenames = [fn+'.todo' for fn in filenames]
    if not settings.EDITOR or settings.EDITOR == 'auto':
        editor = find_first_editor()
    else:
        editor = settings.EDITOR
    os.system(editor + " " +
              " ".join([os.path.join(settings.APP_DIRECTORY, fn) for fn in full_filenames]))


def show_topics(args):
    taskpool = get_taskpool()
    all_tasks = taskpool.tasks + taskpool.special_tasks
    topics = list(set.union(*[set(task.topics) for task in all_tasks]))
    topics.sort()
    for topic in topics:
        print(topic)


def done(args):
    lists_dir = settings.APP_DIRECTORY
    for filename in args.files:
        _from, _to = os.path.join(lists_dir, filename + ".done"), os.path.join(lists_dir, filename + ".todo")
        print("moving {} to {}".format(_from, _to))
        os.rename(_from, _to)


def undo(args):
    lists_dir = settings.APP_DIRECTORY
    for filename in args.files:
        _from, _to = os.path.join(lists_dir, filename + ".done"), os.path.join(lists_dir, filename + ".todo")
        print("moving {} to {}".format(_from, _to))
        os.rename(_from, _to)


def main():
    """
    Entrypoint
    """
    parser = argparse.ArgumentParser(description='console timekeeper')
    subparsers = parser.add_subparsers()
    parser_check = subparsers.add_parser('check',
                                         help='Quick check current '
                                              'scheduled tasks')
    parser_check.set_defaults(func=check)

    parser_scheduled = subparsers.add_parser('scheduled',
                                             help='Show scheduled tasks')
    parser_scheduled.set_defaults(func=scheduled)

    parser_list = subparsers.add_parser('list', help='List all tasks')
    parser_list.add_argument("topic", nargs="*")
    parser_list.add_argument("--no-total", action="store_true",
                             help="do not count total work hours")
    parser_list.add_argument("--unscheduled", action="store_true",
                             help="show unscheduled tasks only")
    parser_list.add_argument("--sort", action="store_true",
                             help="sort output by duration_left")
    parser_list.add_argument("--set_attr", help="set custom attr")
    parser_list.set_defaults(func=list_topic, topic=None)

    parser_today = subparsers.add_parser('today', help='Lists tasks for today')
    parser_today.set_defaults(func=today)

    parser_random = subparsers.add_parser('random',
                                          help='Show ten random tasks')
    parser_random.add_argument("--no-total", action="store_true",
                               help="do not count total work hours")

    parser_random.set_defaults(func=random_tasks)

    parser_edit = subparsers.add_parser('edit',
                                        help='start default system editor'
                                             ' for all todo files')
    parser_edit.add_argument("filenames", nargs="*")
    parser_edit.set_defaults(func=edit)

    parser_topics = subparsers.add_parser('topics',
                                          help='show topic list '
                                               'and some stats')
    parser_topics.set_defaults(func=show_topics)

    parser_done = subparsers.add_parser('done',
                                        help='mark file as done')
    parser_done.add_argument("files", nargs="+",
                             help="file names to be marked as done")
    parser_done.set_defaults(func=done)

    parser_undo = subparsers.add_parser('undo',
                                        help='revert done file to todo')
    parser_undo.add_argument("files", nargs="+",
                             help="done file names to be reverted")
    parser_undo.set_defaults(func=undo)

    if len(sys.argv) < 2:
        args = parser.parse_args(['check'])
    elif sys.argv[1] == "current":
        args = parser.parse_args(['list', 'current'])
    else:
        args = parser.parse_args()

    args.func(args)


if __name__ == '__main__':
    main()
