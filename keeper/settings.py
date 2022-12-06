# -*- coding:utf8 -*-
import os


EDITOR = 'auto'  # set your preferred editor here or 'auto' to look for editors from `POSSIBLE_EDITORS` list

# editors to try if `EDITOR = auto`
POSSIBLE_EDITORS = ['xed', 'gedit', 'vim', 'nano', 'emacs']


TIME_POOLS = {'work', 'personal'}


IGNORED_SECTIONS = {'done', 'debts', 'delegated', 'wontdo', 'library',
                    'scratch', 'optional', 'paid', 'ext', 'external',
                    'extern', 'library', 'passwords'}

SYNONYMS = {'ext': 'external'}

HARD_PAGE_TIME = 0.2
EASY_PAGE_TIME = 0.1

# application directory (e.g. `~/.keeper` expanded to full `/home/<user>/.keeper` on Linux)
APP_DIRECTORY = os.path.expanduser('~/.keeper')

# on first import try to find .keeperrc in home dir. If it is there, execute it
rc_file = os.path.expanduser('~/.keeperrc')

# update locals() from .keeperrc file
if os.path.exists(rc_file):
    with open(rc_file) as f:
        exec(f.read())
