#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup



if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()



classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Office/Business :: Scheduling',
]

setup(
    name='keeper',
    version='0.2.1',
    description='Keeper the console time management tool',
    long_description=readme,
    packages=['keeper'],
    install_requires=['timespans'],
    author='Eugene Katsevman',
    author_email='python@chrisstreeter.com',
    url='https://github.com/eugene-katsevman/keeper',
    license='GPL3+',
    classifiers=classifiers,
    entry_points={'console_scripts':['keeper = keeper.main:main']}
)
