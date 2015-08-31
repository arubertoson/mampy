"""
This module provides utility functions that are useful for general maya
script development. These can also be useful for external purposes.
"""

import functools
import collections

import maya.cmds as cmds


def history_chunk(func):
    """
    History chunk decorator.

    Wraps function inside a history chunk enabling undo chunks to be created
    on python functions.
    """
    @functools.wraps
    def wrapper(*args, **kwargs):
        cmds.undoInfo(openChunk=True)
        try:
            result = func(*args, **kwargs)
        except:
            cmds.undoInfo(closeChunk=True)
            cmds.undo()
            raise
        else:
            cmds.undoInfo(closeChunk=True)
        return result
    return wrapper


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
            raise KeyError(key)

        val = cmds.optionVar(q=key)
        if isinstance(val, list):
            val = OptionVarList(val, key)
        return val

    def __setitem__(self, key, val):
        if isinstance(val, basestring):
            return cmds.optionVar(stringValue=[key, val])

        elif isinstance(val, (int, bool)):
            return cmds.optionVar(intValue=[key, int(val)])

        elif isinstance(val, float):
            return cmds.optionVar(floatValue=[key, val])

        elif isinstance(val, (set, list, tuple, xrange)):
            if len(val) == 0:
                return cmds.optionVar(clearArray=key)

            sequencetype = type(iter(val).next())
            if issubclass(sequencetype, basestring):
                flag = 'stringValue'
            elif issubclass(sequencetype, int):
                flag = 'intValue'
            elif issubclass(sequencetype, float):
                flag = 'floatValue'
            else:
                raise TypeError(
                    '{0!r} is unsupported, valid types are; '
                    'strings, ints and floats.'.format(sequencetype)
                )

            flag += 'Append'
            for each in val:
                cmds.optionVar(**{flag: [key, each]})

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def pop(self, key):
        val = cmds.optionVar(q=key)
        cmds.optionVar(remove=key)
        return val

    __delitem__ = pop

    def keys(self):
        return cmds.optionVar(list=True)


class OptionVarList(tuple):

    def __new__(cls, val, key):
        return tuple.__new__(cls, val)

    def __init__(self, val, key):
        self.key = key

    def append(self, val):
        """Appends given value to end of optionVar list."""
        if isinstance(val, basestring):
            return cmds.optionVar(stringValueAppend=[self.key, val])

        elif isinstance(val, int):
            return cmds.optionVar(intValueAppend=[self.key, val])

        elif isinstance(val, float):
            return cmds.optionVar(floatValueAppend=[self.key, val])

        else:
            raise TypeError(
                'Unsupported datatype. Valid types; strings, ints and floats.'
            )
