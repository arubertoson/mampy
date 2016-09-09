"""
"""
import logging
import textwrap
import collections

from maya import cmds, mel
from maya.api import OpenMaya as api

logger = logging.getLogger(__name__)


class OptionVar(collections.MutableMapping):
    """
    Dictionary class for accessing and modifying optionVars.

    Inspired by pymel OptionVarDict class found in pymel.core.language.
    """
    def __call__(self, *args, **kwargs):
        return cmds.optionVar(*args, **kwargs)

    def __contains__(self, key):
        return bool(cmds.optionVar(exists=key))

    def __getitem__(self, key):
        if key not in self:
            raise KeyError()

        val = cmds.optionVar(q=key)
        if isinstance(val, (list)):
            val = OptionVarList(val, key)
        return val

    def __setitem__(self, key, val):
        if isinstance(val, basestring):
            return cmds.optionVar(stringValue=(key, val))

        elif isinstance(val, (int, bool)):
            return cmds.optionVar(intValue=(key, val))

        elif isinstance(val, float):
            return cmds.optionVar(floatValue=(key, val))

        elif isinstance(val, (set, list, tuple, xrange)):
            if len(val) == 0:
                return cmds.optionVar(ca=True)

            seq_type = type(iter(val).next())
            if issubclass(seq_type, basestring):
                flag = 'stringValue'
            elif issubclass(seq_type, int):
                flag = 'intValue'
            elif issubclass(seq_type, float):
                flag = 'floatValue'
            else:
                raise TypeError(
                    '{0!r} is unsupported, valid types are; '
                    'strings, ints and floats.'.format(seq_type)
                )
            flag += 'Append'
            for each in val:
                cmds.optionVar(**{flag: (key, each)})

    def __len__(self):
        return self.keys()

    def pop(self, key):
        val = cmds.optionVar(q=key)
        cmds.optionVar(remove=key)
        return val

    __delitem__ = pop

    def iterkeys(self):
        return iter(self.keys())

    __iter__ = iterkeys

    def keys(self):
        return cmds.optionVar(list=True)


class OptionVarList(collections.Sequence):

    def __init__(self, items, key):
        self.items = items
        self.key = key
        self.type = type(items[0])
        if self.type in (unicode, str):
            self.type = basestring

    def __repr__(self):
        return '{}({}({}))'.format(self.__class__.__name__, self.key,
                                   self.items)

    def __str__(self):
        return '{}'.format(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

    def __reversed__(self):
        cmds.optionVar(clearArray=self.key)
        for i in reversed(self.items):
            self.append(i)

    def pop(self, idx):
        val = self.items.pop(idx)
        cmds.optionVar(removeFromArray=(self.key, idx))
        return val

    def clear(self):
        cmds.optionVar(clearArray=self.key)

    def append(self, val):
        """
        Appends given value to end of optionVar list.
        """
        if not isinstance(val, self.type):
            raise TypeError('Valid type for {} is {}, value given was: {}'
                            .format(self.key, self.type, type(val)))

        if isinstance(val, int):
            cmds.optionVar(intValueAppend=(self.key, val))
        elif isinstance(val, basestring):
            cmds.optionVar(stringValueAppend=(self.key, val))
        elif isinstance(val, float):
            cmds.optionVar(floatValueAppend=(self.key, val))
        else:
            raise TypeError('Valid type for {} is {}'.format(self.key,
                            self.type))
        self.items = cmds.optionVar(q=self.key)


class MelGlobals(collections.Mapping):

    MELTYPES = {'string': str, 'int': int, 'float': float,
                'vector': api.MVector}
    TYPE_MAP = {}
    key_values = {}

    def __init__(self, *args, **kwargs):
        super(MelGlobals, self).__init__(*args, **kwargs)
        self._globals = mel.eval('env;')

    def __getitem__(self, key):
        try:
            return self.key_values[key]
        except KeyError:
            r = self.get(key)
            self.key_values[key] = r
            return r

    def __iter__(self):
        for var in self._globals:
            if var.startswith('$'):
                var = var[1:]
            yield var

    def __len__(self):
        return len(self._globals)

    def _format_var(self, var):
        if not var.startswith('$'):
            var = '$' + var
        if var.endswith('[]'):
            var = var[:-2]
        return var

    def _get_var_type(self, var):
        try:
            return self.TYPE_MAP[var]
        except KeyError:
            pass

        t = mel.eval('whatIs "{}"'.format(var)).split()
        if t[0].startswith('Unknown'):
            raise KeyError('{}'.format(var))

        if len(t) == 2 and t[1].startswith('variable'):
            self.TYPE_MAP[var] = t[0]
            return t[0]
        raise TypeError('Cannot determine type of {}'.format(var))

    def _get_declare(self, type, var):
        if type.endswith('[]'):
            type = type[:-2]
            var += '[]'
        return 'global {} {}'.format(type, var)

    def get(self, var, type=None):

        var = self._format_var(var)
        if type is None:
            type = self._get_var_type(var)

        if type.endswith('[]'):
            proc_name = 'mampy_get_global_' + var[1:].replace('[]', 'array')
        else:
            proc_name = 'mampy_get_global_' + type

        try:
            global_declare = self._get_declare(type, var)
            cmd = textwrap.dedent('''
                global proc {type} {proc_name}()
                {{
                    {global_declare};
                    return {var};
                }}
                {proc_name}()
            '''.format(**locals()))
            result = mel.eval(cmd)
        except RuntimeError:
            raise RuntimeError('{} is an undeclared variable.'.format(var))

        try:
            if type.endswith('[]'):
                return tuple(mel.eval(cmd))
            else:
                return self.MELTYPES[type](mel.eval(cmd))
        except RuntimeError:
            raise RuntimeError('{}'.format(cmd))

