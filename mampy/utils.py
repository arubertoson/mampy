# -*- coding: utf-8 -*-

"""
    mampy.utils
    ~~~~~~~~~~~

"""
import functools
import collections

import maya.cmds as cmds
import maya.api.OpenMaya as api

from .component import Component
from .nodes import DagNode


def history_chunk(func):
    """
    Wraps function inside a history chunk enabling undo for scripts inside
    Maya.
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


class SelectionList(object):
    """Sequence object that wraps MSelectionList from new maya api.

    Emulates the api MSelectionList while trying to behave like a list
    object. The main difference is that iter iterates over the string list,
    to iterate over MObjects use the itercomps/iterdags.

    The sequence always returns either a Component or DagPath, these are
    custom classes that wraps MObjects and MDagPaths to behave more like
    python objects.
    """

    def __init__(self, slist=None, merge=True):
        if isinstance(slist, api.MSelectionList):
            self._slist = api.MSelectionList(slist)

        elif type(slist) in [set, list, tuple]:
            self._slist = api.MSelectionList()
            for dagstr in slist:
                tmp = api.MSelectionList(); tmp.add(dagstr)
                dp, comp = tmp.getComponent(0)
                if comp.isNull():
                    self._slist.add(dp, mergeWithExisting=merge)
                else:
                    self._slist.add((dp, comp), mergeWithExisting=merge)
        else:
            self._slist = api.MSelectionList()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{}'.format(list(self))

    def __getitem__(self, key):
        if isinstance(key, slice):
            raise TypeError('{} does not support slice.'
                            .format(self.__class__.__name__))

        mdag, mobj = self._slist.getComponent(key)
        if mobj.isNull():
            return DagNode(mdag)
        return Component(mdag, mobj)

    def __len__(self):
        return self._slist.length()

    def __iter__(self):
        """
        Since the only viable way to interate an MSelectionList is by idx
        and that's pretty well covered with xrange(len(self)) iter is used
        to create the stringlist, which can easily be passed to cmds commands.
        """
        return iter(self._slist.getSelectionStrings())

    def __contains__(self, value):
        if type(value) == tuple:
            return self._slist.hasItemPartly(*value)
        return self._slist.hasItem(value)

    def __eq__(self, other):
        return list(self) == list(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return bool(len(self))

    def __hash__(self):
        return hash(list(self))

    @classmethod
    def from_ls(cls, merge=True, **kwargs):
        return cls(cmds.ls(**kwargs), merge)

    @classmethod
    def from_selection(cls):
        return cls(api.MGlobal.getActiveSelectionList())

    @classmethod
    def from_ordered(cls, start=None, stop=None, step=None, **kwargs):
        return cls(cmds.ls(os=True)[slice(start, stop, step)], False)

    def append(self, value):
        if isinstance(value, basestring):
            self._slist.add(value)
        elif isinstance(value, (DagNode, Component)):
            self._slist.add(value.node, mergeWithExisting=False)
        else:
            self._slist.add(value, mergeWithExisting=False)

    def extend(self, other, strategy=api.MSelectionList.kMergeNormal):
        if type(other) == tuple:
            mdag, mobj = other
            self._slist.merge(mdag, mobj, strategy)
        else:
            self._slist.merge(other._slist, strategy)

    def copy(self):
        return self.__class__(api.MSelectionList().copy(self._slist))

    def toggle(self, other):
        self.extend(other, api.MSelectionList.kXORWithList)

    def remove(self, other):
        self.extend(other, api.MSelectionList.kRemoveFromList)

    def pop(self, index):
        value = self[index]
        self._slist.remove(index)
        return value

    __delitem__ = pop

    def itercomps(self):
        for idx in xrange(len(self)):
            yield Component(*self._slist.getComponent(idx))

    def iterdags(self):
        for idx in xrange(len(self)):
            yield DagNode(self._slist.getDagPath(idx))


class OptionVar(collections.MutableMapping):
    """Dictionary class for accessing and modifying optionVars.

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
    """Sequence of option var key list."""

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
