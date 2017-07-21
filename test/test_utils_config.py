"""
Tests for mampy.utils.config module
"""
import os
import json
import tempfile
import contextlib

import mock
import pytest

from mampy.utils.config import Config, get_system_config_directory
from mampy.utils.external.pathlib2 import Path


@mock.patch('sys.platform', 'win32')
def test_system_config_directory_windows():
    appdata = 'C:\Users\test\Appdata\roaming'
    with mock.patch.dict(os.environ, {'APPDATA': appdata}):
        assert str(get_system_config_directory()) == appdata


@mock.patch('sys.platform', 'darwin')
def test_system_config_directory_windows():
    home = '/user'
    with mock.patch.dict(os.environ, {'HOME': home}):
        pref = os.path.join(os.path.expanduser('~'), 'Library', 'Preferences')
        assert get_system_config_directory() == pref


@mock.patch('sys.platform', 'Linux')
def test_system_config_directory_windows():
    home = '/user/config'
    with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': home}):
        assert str(get_system_config_directory()) == home


@pytest.fixture
def configfile(tmpdir):
    return tmpdir.mkdir('mampy').join('.mampytest')


def test_empty_config_dictionary(configfile):
    assert not Config(str(configfile))


def test_create_file(configfile):
    json_data = '{"Key": "hello"}'
    configfile.write(json_data)
    assert Config(str(configfile))


def test_add_new_value_to_config_dictionary(configfile):
    config = Config(str(configfile))
    config['TESTY'] = 'value'
    assert 'TESTY' in config


def test_add_new_value_to_config_dictionary_file(configfile):
    Config(str(configfile))['TESTY'] = 'value'
    assert 'TESTY' in json.loads(configfile.read())
