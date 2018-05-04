# -*- coding:utf8 -*-
import os


EDITOR = 'auto'

IGNORED_SECTIONS = {'done', 'debts', 'delegated', 'wontdo', 'library',
                    'scratch', 'optional', 'paid', 'ext', 'external',
                    'extern', 'library', 'passwords'}

SYNONYMS = {'ext': 'external'}

HARD_PAGE_TIME = 0.2
EASY_PAGE_TIME = 0.1

# on first import try to find .keeperrc in home dir. If it is there, execute it

rc_file = os.path.expanduser('~/.keeperrc')

try:
    with open(rc_file) as f:
        exec(f.read())
except FileNotFoundError:
   pass
