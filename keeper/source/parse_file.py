import os
import re
import typing

from keeper.source.parse import Attributes
from keeper.source.abstract import SourceLine

from keeper.source.parse import extract_attributes
from keeper.source.parse import get_indent_level
from keeper.task import Task


class TaskLine(SourceLine):
    """
    bidirectional interface to task as stored in a file
    """

    @property
    def name(self) -> str:
        filename = self.source.filename
        return os.path.splitext(os.path.basename(filename))[0]

    def _parse(self):
        """
        recapture attribute collections
        :return: nothing
        """
        self.attr_collections = []
        index = self.line.find('[')
        while index != -1:
            end_index = self.line.find(']', index)
            self.attr_collections.append(
                Attributes(index + 1, self.line[index + 1:end_index]))
            index = self.line.find('[', end_index)

    @property
    def pure_name(self):
        return re.sub(r'\[.*?\]', '', self.line)

    def __init__(self, line, source=None):
        SourceLine.__init__(self, line)
        self.source = source

    def __str__(self):
        return "{} with attr collections ({})".format(self.line,
                                                      self.attr_collections)

    def has_attr(self, value):
        for collection in self.attr_collections:
            for attr in collection.attrs:
                if attr.value == value:
                    return True
        return False

    def set_attr(self, value):
        if not self.has_attr(value):
            self.add_attr(value)

    def add_attr(self, value):
        """
        :param value: new attribute to add to the line
        :return:
        """
        if not self.attr_collections:
            self.line += ' [{}]'.format(value)
        else:
            collection = self.attr_collections[-1]
            self.line = (self.line[:collection.location + len(collection.text)]
                         + ", " + value +
                         self.line[collection.location+len(collection.text):])
        self._parse()

    def remove_attr_by_value(self, value):
        for collection in reversed(self.attr_collections):
            for i, attr in enumerate(reversed(collection.attrs)):
                if attr.value == value:
                    self.line = (self.line[:attr.location] +
                                 self.line[attr.location+len(attr.text) +
                                           (1 if i != 0 else 0):])
        self._parse()

        for collection in reversed(self.attr_collections):
            if collection.is_empty():
                self.line = (self.line[:collection.location-1] +
                             self.line[collection.location +
                                       len(collection.text)+1:])
        self._parse()

    def save(self):
        self.source.save()


class TaskTuple(typing.NamedTuple):
    level: int
    task: Task


class TasksSourceFile:
    def __init__(self, filename=None, stream=None):
        self.tasks = []
        self.special_tasks = []
        self.lines = []
        self.filename = filename
        if stream:
            self._load_from_stream(stream, filename=filename)
        elif filename:
            self._load_from_file(filename)

    def _load_from_stream(self, stream, filename=None):
        task_stack = []
        current_section = None
        section_attributes = dict()
        in_comment = False
        prev_level, level = 0, 0
        self.lines = [TaskLine(line.rstrip()) for line in stream.readlines()]
        for lineno, source_line in enumerate(self.lines):
            line = source_line.line
            if line:
                if in_comment and "*/" in line:
                    in_comment = False
                    continue
                if in_comment:
                    continue
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('#'):
                    pass
                elif stripped.startswith("/*"):
                    in_comment = True
                elif line.endswith(':'):
                    current_section = line.strip()[:-1]
                    section_attributes = extract_attributes(current_section)
                    current_section = re.sub(r'\[.*\]', '', current_section)
                    current_section = re.sub(r'[ ]+', ' ',
                                             current_section.strip())
                else:
                    prev_level, level = level, get_indent_level(line)
                    if not level:
                        current_section = None
                        section_attributes = dict()

                    taskline = TaskLine(line, source=self)
                    attributes = dict()
                    attributes.update(section_attributes)
                    attributes.update(extract_attributes(line))
                    attributes['topic'] = current_section
                    attributes['topics'] += \
                        [os.path.basename(filename).split('.')[0]]

                    attributes['topics'] += section_attributes.get('topics', [])
                    if current_section:
                        attributes['topics'].append(current_section)

                    attributes['source'] = taskline
                    while task_stack and task_stack[-1].level >= level:
                        task_stack.pop(-1)
                    attributes['parent'] = None if not task_stack else task_stack[-1].task

                    task = Task(**attributes)

                    self.add_task(task)
                    self.lines[lineno] = taskline
                    task_stack.append(TaskTuple(level=level, task=task))

    def _load_from_file(self, filename):
        with open(filename) as f:
            self._load_from_stream(stream=f, filename=filename)

    def save(self):
        with open(self.filename, 'w') as f:
            f.writelines(source_line.line + '\n' for source_line in self.lines)

    def add_task(self, task, first=False):
        if task.is_ignored():
            if not first:
                self.special_tasks.append(task)
            else:
                self.special_tasks.insert(0, task)
        else:
            if not first:
                self.tasks.append(task)
            else:
                self.tasks.insert(0, task)

    def insert_after(self, line: TaskLine, after: int):
        line.source = self
        self.lines.insert(after + 1, line)

    def insert_before(self, line: TaskLine, before: int):
        line.source = self
        self.lines.insert(before, line)
