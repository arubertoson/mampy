"""
Config helper
"""
import os
import sys
import json
import yaml
import ast
import simplejson

from mampy.utils.external.pathlib2 import Path


def get_system_config_directory():
    """ Return platform specific config directory.
    """
    try:
        return {
            'win32':
                os.path.abspath(os.getenv('APPDATA')),
            'darwin':
                os.path.join(os.path.expanduser('~'), 'Library', 'Preferences')
        }[sys.platform]
    except KeyError:
        return os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~')


class Config(dict):
    """
    A helper class to ease use of json by reading and writing to the
    specified file when a value is added or changed.
    """

    def __init__(self, file_):
        self._initialized = False
        self._file = Path(file_)
        self._file.parent.mkdir(exist_ok=True)

        if self._file.exists():
            data = self.data
            super(Config, self).__init__(data)
        else:
            with self._file.open('w') as json_file:
                json_file.write(unicode(json.dumps('{}')))
        self._initialized = True

    @property
    def data(self):
        with self._file.open('r') as json_file:
            return json.loads(json_file.read())

    def __setitem__(self, key, value):
        super(Config, self).__setitem__(key, value)
        if self._initialized:
            self.dumps()

    def dumps(self, data=None):
        with self._file.open('w') as json_file:
            json_file.write(
                unicode(
                    json.dumps(
                        data or self, indent=2, sort_keys=4,
                        ensure_ascii=False)))
