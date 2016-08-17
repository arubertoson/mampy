# -*- coding: utf-8 -*-
"""
Module to store containers.
"""
import logging
from abc import ABCMeta, abstractmethod

from maya import cmds
from maya.api import OpenMaya as api


from mampy.comps import Component
from mampy.nodes import DagNode, DependencyNode, Plug

logger = logging.getLogger(__name__)


class AbstractSelectionList(object):
    __metaclass__ = ABCMeta

    def __init__(self, elements=None, merge=True):
        self._slist = api.MSelectionList()
        self._populate_list(elements, merge)

    def _populate_list(self, elements, merge):
        if elements is not None:
            if isinstance(elements, api.MSelectionList):
                self._slist = self._slist.merge(elements)
            else:
                for element in elements:
                    self._slist.add(element)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return str(list(i for i in self))

    def __len__(self):
        return self._slist.length()

    def __eq__(self, other):
        return list(self) == list(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return bool(len(self))

    def __hash__(self):
        return hash(str(self))

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __contains__(self, other):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @classmethod
    def from_selection(cls):
        return cls(cmds.ls(sl=True))

    @classmethod
    def from_ls(cls, merge=False, *args, **kwargs):
        if not merge:
            merge = True if 'fl' in kwargs or 'flatten' in kwargs else False
        return cls(cmds.ls(*args, **kwargs), merge)

    def append(self, value):
        if isinstance(value, basestring):
            self._slist.add(value)
        else:
            self._slist.add(value.node, mergeWithExisting=False)

    def copy(self):
        return self.__class__(api.MSelectionList().copy(self._slist))

    def clear(self):
        return self._slist.clear()

    def extend(self, other, strategy=api.MSelectionList.kMergeNormal):
        self._slist.merge(other._slist, strategy)

    def pop(self, index=None):
        index = len(self)-1 if index is None else index
        value = self[index]
        self.remove(index)
        return value

    __delitem__ = pop

    def replace(self, value, other):
        return self._slist.replace(value, other)

    def remove(self, value):
        return self._slist.remove(value)


class ComponentList(AbstractSelectionList):

    def __init__(self, elements=None, merge=True):
        super(ComponentList, self).__init__(elements, merge)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(
                [self._slist.getComponent(i) for i in xrange(*key.indices(len(self)))]
            )
        else:
            return Component(self._slist.getComponent(key))

    def __iter__(self):
        return (Component(self._slist.getComponent(i)) for i in xrange(len(self)))

    def __contains__(self, other):
        return self._slist.hasItemPartly(*other.node)

    def toggle(self, component):
        return self._slist.toggle(*component)


class DagbaseList(AbstractSelectionList):

    def __init__(self, object, elements=None, merge=True):
        super(DagbaseList, self).__init__(elements, merge)
        self._object = object
        self._get_func = {
            DagNode: 'getDagPath',
            DependencyNode: 'getDependNode',
            Plug: 'getPlug',
        }[self._object]

    def __iter__(self):
        get = getattr(self._slist, self._get_func)
        for x in xrange(len(self)):
            yield self._object(get(x))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__([
                getattr(self._slist, self._get_func)(i)
                for i in xrange(*key.indices(len(self)))
            ])
        else:
            return self._object(getattr(self._slist, self._get_func)(key))

    def __contains__(self, other):
        return self._slist.hasItem(other)

    @classmethod
    def from_name(cls, name):
        return cls(api.MGlobal.getSelectionListByName(name))

    @classmethod
    def from_hilited(cls, *args, **kwargs):
        return cls(cmds.ls(hl=True, *args, **kwargs))


class DagpathList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(DagpathList, self).__init__(DagNode, dagpath, merge)


class DependencyList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(DependencyList, self).__init__(DependencyNode, dagpath, merge)


class PlugList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(PlugList, self).__init__(Plug, dagpath, merge)

