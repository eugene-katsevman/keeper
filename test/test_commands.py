# coding: utf-8
"""
Functional tests for console command syntax
"""

import os
import sys
import pytest
import unittest.mock

from keeper import main, settings


@unittest.mock.patch('os.system')
def test_edit_command_default(os_system):
    """
    check that `keeper edit` command will open all `~/.keeper/*.todo` files
    """
    sys.argv = ["keeper", "edit"]
    homedir = os.path.expanduser('~')
    settings.EDITOR = 'testeditor'
    main.main()
    os_system.assert_called_once_with('testeditor {homedir}/.keeper/*.todo'.format(**locals()))


@unittest.mock.patch('os.system')
def test_edit_command_w_filenames(os_system):
    """
    check that `keeper edit <filename>` command will open `~/.keeper/<filename>.todo` file
    """
    sys.argv = ["keeper", "edit", "main", "test"]
    homedir = os.path.expanduser('~')
    settings.EDITOR = 'testeditor'
    main.main()
    os_system.assert_called_once_with('testeditor {homedir}/.keeper/main.todo {homedir}/.keeper/test.todo'\
                                      .format(**locals()))


@unittest.mock.patch('os.system')
def test_edit_command_w_filenames_w_extensions(os_system):
    """
    check that `keeper edit <filename>.todo` (filename with extension)
    command will open `~/.keeper/<filename>.todo` file
    """
    sys.argv = ["keeper", "edit", "main.todo", "test"]
    homedir = os.path.expanduser('~')
    settings.EDITOR = 'testeditor'
    main.main()
    os_system.assert_called_once_with('testeditor {homedir}/.keeper/main.todo {homedir}/.keeper/test.todo'\
                                      .format(**locals()))


@unittest.mock.patch('os.system')
def test_edit_command_w_autoeditor(os_system):
    """
    check that `keeper edit <filename>` will use first of `settings.POSSIBLE_EDITORS` editors
    when `settings.EDITOR = 'auto'`
    """
    settings.EDITOR = 'auto'
    sys.argv = ["keeper", "edit", "main"]
    homedir = os.path.expanduser('~')
    default_editor = settings.POSSIBLE_EDITORS[0]
    main.main()
    os_system.assert_called_once_with('{default_editor} {homedir}/.keeper/main.todo'.format(**locals()))


def test_edit_command_no_editor():
    """
    check that `keeper edit <filename>` command will raise RuntimeError without available editors
    """
    sys.argv = ["keeper", "edit", "main"]
    settings.EDITOR = 'auto'
    settings.POSSIBLE_EDITORS = []

    with pytest.raises(RuntimeError):
        main.main()

