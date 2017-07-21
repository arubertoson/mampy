# -*- coding: utf-8 -*-
"""
Module to store containers.
"""
from __future__ import absolute_import, unicode_literals

import logging
from abc import ABCMeta, abstractmethod

from maya import cmds
from maya.api import OpenMaya as api


from mampy.core.components import SingleIndexComponent
from mampy.core.dagnodes import Node, DependencyNode, Plug
from mampy.core.exceptions import OrderedSelectionsNotSet

logger = logging.getLogger(__name__)


class AbstractSelectionList(object):
    __metaclass__ = ABCMeta

    def __init__(self, elements=None, merge=True):
        self._slist = api.MSelectionList()
        self._populate_list(elements, merge)

    @abstractmethod
    def _populate_list(self, elements, merge):
        pass

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return str(list(i for i in self))

    def __len__(self):
        return self._slist.length()

    def __eq__(self, other):
        return set(self.cmdslist()) == set(other.cmdslist())

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
    def from_ls(cls, *args, **kwargs):
        merge = True
        if any(i in kwargs for i in ('fl', 'flatten', 'os', 'orderedSelection')):
            if not cmds.selectPref(q=True, trackSelectionOrder=True):
                raise OrderedSelectionsNotSet()
            merge = False

        if 'merge' in kwargs:
            merge = kwargs['merge']
        return cls(cmds.ls(*args, **kwargs), merge)

    def append(self, other):
        if isinstance(other, basestring):
            self._slist.add(other)
        else:
            try:
                self._slist.add(other.node, mergeWithExisting=False)
            except (TypeError, ValueError):
                self._slist.add(other.dagpath, mergeWithExisting=False)

    def copy(self):
        return self.__class__(api.MSelectionList().copy(self._slist))

    def clear(self):
        return self._slist.clear()

    def extend(self, other, merge=True, strategy=api.MSelectionList.kMergeNormal):
        if isinstance(other, (self.__class__, api.MSelectionList)):
            try:
                self._slist.merge(other._slist, strategy)
            except RuntimeError:
                pass
        else:
            for each in other:
                self._slist.add(each.node, mergeWithExisting=merge)

    def pop(self, index=None):
        index = len(self)-1 if index is None else index
        value = self[index]
        self.remove(index)
        return value

    __delitem__ = pop

    def replace(self, index, other):
        return self._slist.replace(index, other)

    def remove(self, index):
        return self._slist.remove(index)

    def cmdslist(self, index=None):
        if index:
            return self._slist.getSelectionStrings(index)
        return self._slist.getSelectionStrings()


def get_borders_from_complist(complist):
    """Get border edges from selection and return a new selection list."""
    border_edges = ComponentList()
    for component in complist:
        borders = component.new()
        for index in component.indices:
            if not component.is_border(index):
                continue
            borders.add(index)
        if borders:
            border_edges.append(borders)
    return border_edges


class ComponentList(AbstractSelectionList):

    def __init__(self, elements=None, merge=True):
        super(ComponentList, self).__init__(elements, merge)

    def _populate_list(self, elements, merge):
        if elements is not None:
            if isinstance(elements, api.MSelectionList):
                self._slist = self._slist.merge(elements)
            else:
                for element in elements:
                    if isinstance(element, basestring):
                        try:
                            element = api.MSelectionList().add(element).getComponent(0)
                        except TypeError:
                            continue
                    self._slist.add(element, merge)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(
                [self._slist.getComponent(i) for i in xrange(*key.indices(len(self)))]
            )
        else:
            return SingleIndexComponent(*self._slist.getComponent(key))

    def __iter__(self):
        return (SingleIndexComponent(*self._slist.getComponent(i)) for i in xrange(len(self)))

    def __nonzero__(self):
        result = super(ComponentList, self).__nonzero__()
        if result:
            return not(all(type(obj) is SingleIndexComponent for obj in self))
        else:
            return result

    def __contains__(self, other):
        return self._slist.hasItemPartly(*other.node)

    def toggle(self, component):
        return self._slist.toggle(*component)


class MultiComponentList(ComponentList):

    def __init__(self, elements=None, merge=True):
        super(MultiComponentList, self).__init__(elements, merge)

    def _sort_elements(self, elements):
        import collections
        multi_map = collections.defaultdict(set)
        for element in elements:
            obj, _ = element.split('[')
            multi_map[obj].add(element)
        return multi_map

    def _populate_list(self, elements, merge):
        if elements is not None:
            for elements in self._sort_elements(elements).itervalues():
                self.append(ComponentList(elements).pop())


class DagbaseList(AbstractSelectionList):

    def __init__(self, object, elements=None, merge=True):
        self._object = object
        self._get_func = {
            Node: 'getDagPath',
            DependencyNode: 'getDependNode',
            Plug: 'getPlug',
        }[self._object]
        super(DagbaseList, self).__init__(elements, merge)

    def _populate_list(self, elements, merge):
        if elements is not None:
            if isinstance(elements, api.MSelectionList):
                self._slist = self._slist.merge(elements)
            else:
                for element in elements:
                    if isinstance(element, basestring):
                        sl = api.MSelectionList().add(element)
                        get = getattr(sl, self._get_func)
                        try:
                            element = get(0)
                        except TypeError:
                            continue
                    elif isinstance(element, Node):
                        element = element.dagpath
                    self._slist.add(element, merge)

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
        return self._slist.hasItem(other.dagpath)

    @classmethod
    def from_name(cls, name):
        return cls(api.MGlobal.getSelectionListByName(name))

    @classmethod
    def from_hilited(cls, *args, **kwargs):
        return cls(cmds.ls(hl=True, *args, **kwargs))


class DagpathList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(DagpathList, self).__init__(Node, dagpath, merge)


class DependencyList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(DependencyList, self).__init__(DependencyNode, dagpath, merge)


class PlugList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(PlugList, self).__init__(Plug, dagpath, merge)
