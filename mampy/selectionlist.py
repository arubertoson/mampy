# -*- coding: utf-8 -*-

"""
    mampy.utils
    ~~~~~~~~~~~

"""
import maya.cmds as cmds
from maya.api import OpenMaya as api

from .component import Component
from .nodes import DagNode


class SelectionList(object):
    """The :class:`SelectionList <SelectionList>` is a sequence object that
    wraps MSelectionList from new maya api.

    Emulates the api MSelectionList while trying to behave like a list
    object. The objects in the list can be fetched by index making the
    __iter__ a bit useless. I've taken advantage of this and made the __iter__
    refer to MSelectionList.getSelectionStrings() to fetch the readable
    string list that maya usually provices through cmds.ls making the
    :class:`SelectionList` easy to pass around.

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
        """
        Constructs a :class:`SelectionList` from ls.

        :param merge: If found components should be merged to one MObject.
        """
        return cls(cmds.ls(**kwargs), merge)

    @classmethod
    def from_selection(cls):
        """
        Constructs a :class:`SelectionList` from selection.
        """
        return cls(api.MGlobal.getActiveSelectionList())

    @classmethod
    def from_ordered(cls, start=None, stop=None, step=None, **kwargs):
        """
        Constructs and returns an ordered :class:`SelectionList`.

        :param start: start of slice.
        :param stop: end of slice.
        :param step: slice steps.
        """
        return cls(cmds.ls(os=True, **kwargs)[slice(start, stop, step)], False)

    def append(self, value):
        """
        Appends a given dagpath to the end of the list.

        :param value: dagpath string, MObject, (MDatPath, MObject) tuple
        """
        if isinstance(value, basestring):
            self._slist.add(value)
        elif isinstance(value, (DagNode, Component)):
            self._slist.add(value.node, mergeWithExisting=False)
        else:
            self._slist.add(value, mergeWithExisting=False)

    def extend(self, other, strategy=api.MSelectionList.kMergeNormal):
        """
        Extends list with given :class:`SelectionList` object or
        :class:`Component`.

        :param strategy: Merge stratgety
        """
        if type(other) == tuple:
            mdag, mobj = other
            self._slist.merge(mdag, mobj, strategy)
        else:
            self._slist.merge(other._slist, strategy)

    def copy(self):
        """
        Returns a copy of self.
        """
        return self.__class__(api.MSelectionList().copy(self._slist))

    def toggle(self, other):
        """
        Toggles other :class:`SelectionList` objects with self.
        """
        self.extend(other, api.MSelectionList.kXORWithList)

    def remove(self, other):
        """
        Removes other :class:`SelectionList` object from self.
        """
        self.extend(other, api.MSelectionList.kRemoveFromList)

    def pop(self, index=-1):
        """
        pops given index from list.
        """
        value = self[index]
        self._slist.remove(index)
        return value

    __delitem__ = pop

    def itercomps(self):
        """
        Iterates over the :class:`SelectionList` :class:`Component` objects.

        .. note:: Not treadsafe.
        """
        for idx in xrange(len(self)):
            yield Component(*self._slist.getComponent(idx))

    def iterdags(self):
        """
        Iterates over the :class:`SelectionList` :class:`DagNode` objects.

        .. note:: Not treadsafe.
        """
        for idx in xrange(len(self)):
            yield DagNode(self._slist.getDagPath(idx))
