"""
# TODO: Better documentation
Module to store containers.
"""
from __future__ import absolute_import, unicode_literals

import logging
from abc import ABCMeta, abstractmethod

from maya import cmds
from maya.api import OpenMaya as api

from mampy.core.components import AbstractComponent, SingleIndexComponent
from mampy.core.dagnodes import Node, DependencyNode, Plug
from mampy.core.exceptions import OrderedSelectionsNotSet

logger = logging.getLogger(__name__)


def is_track_order_set():
    return cmds.selectPref(q=True, trackSelectionOrder=True)


def need_ordered_selection_set(kwargs):
    return any(i in kwargs for i in ('fl', 'flatten', 'os', 'orderedSelection'))


class AbstractSelectionList(object):
    __metaclass__ = ABCMeta

    def __init__(self, elements=None, merge=True):
        self._cache = {}
        self._slist = api.MSelectionList()
        if elements is not None:
            self._process_dispatcher(elements, merge)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return str(self._slist)

    def __eq__(self, other):
        if len(self) == len(other):
            return all(
                self._slist.hasItem(other._slist.getComponent(x))
                for x in xrange(len(other))
            )
        return False

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __nonzero__(self):
        return not (self._slist.isEmpty())

    def __hash__(self):
        return hash(self._slist)

    def __len__(self):
        return self._slist.length()

    def __copy__(self):
        new = self.__class__(api.MSelectionList().copy(self._slist))
        new._cache = self._cache
        return new

    def __iter__(self):
        for i in xrange(len(self)):
            yield self._process_cache(i)

    @abstractmethod
    def _process_cache(self, key):
        pass

    def __getitem__(self, key):
        return self._process_cache(len(self) - 1 if key == -1 else key)

    @abstractmethod
    def __contains__(self, other):
        pass

    @abstractmethod
    def _process_dispatcher(self, elements, merge):
        pass

    @classmethod
    def from_selection(cls):
        return cls(api.MGlobal.getActiveSelectionList())

    @classmethod
    def from_ls(cls, *args, **kwargs):
        # Assume that we want to merge the selection list
        merge = True
        if need_ordered_selection_set():
            if not is_track_order_set():
                raise OrderedSelectionsNotSet()
            # If we are tracking order we can't merge the components
            merge = False

        if 'merge' in kwargs:
            merge = kwargs.pop('merge')
        return cls(cmds.ls(*args, **kwargs), merge)

    @abstractmethod
    def append(self, other, merge=False):
        pass

    @abstractmethod
    def extend(self, other):
        pass

    @abstractmethod
    def replace(self, index, other):
        pass

    def pop(self, index=-1):
        value = self[index]
        self.remove(len(self) - 1 if index == -1 else index)
        return value

    __delitem__ = pop

    def remove(self, index):
        self._cache.pop(index, None)
        return self._slist.remove(index)

    def cmdslist(self, index=None):
        if index:
            return self._slist.getSelectionStrings(index)
        return self._slist.getSelectionStrings()


def get_borders_from_complist(complist):
    """Get border edges from selection and return a new selection list.

    TODO: In wrong module.
    """
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


# TODO: These functions should be moved to a utils
def get_component_from_input(input):
    try:
        return api.MSelectionList().add(input).getComponent(0)
    except TypeError:
        return None


def is_valid_maya_component(element):
    try:
        return not (element[1].isNull())
    except TypeError:
        return False


def is_maya_string_component(element):
    return len(element.split('.')) > 1


def is_component_list(mlist):
    return not (mlist.getComponent(0)[1].isNull())


class ComponentList(AbstractSelectionList):
    def __init__(self, elements=None, merge=True):
        super(ComponentList, self).__init__(elements, merge)

    def _process_strings(self, string_components, merge):
        for strcomp in string_components:
            comp = get_component_from_input(strcomp)
            if comp is None:
                continue
            self._slist.add(comp, merge)

    def _process_components(self, maya_components, merge):
        for each in maya_components:
            self._slist.add(get_component_from_input(each), merge)

    def _process_mlist(self, mlist, merge):
        if is_component_list(mlist):
            self._slist = mlist

    def _process_dispatcher(self, elements, merge):
        if isinstance(elements, api.MSelectionList):
            return self._process_mlist(elements, merge)

        element = iter(elements).next()
        if isinstance(element, basestring):
            if is_maya_string_component(element):
                return self._process_strings(elements, merge)
        else:
            if is_valid_maya_component(element):
                return self._process_components(elements, merge)

        raise TypeError(
            '{} is invalid type for {}.'.
            format(type(element), self.__class__.__name__)
        )

    def _process_cache(self, key):
        try:
            return self._cache[key]
        except KeyError:
            sic = SingleIndexComponent(*self._slist.getComponent(key))
            self._cache[key] = sic
            return sic

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(
                [
                    self._slist.getComponent(i)
                    for i in xrange(*key.indices(len(self)))
                ]
            )
        else:
            return super(ComponentList, self).__getitem__(key)

    def __contains__(self, other):
        try:
            return self._slist.hasItemPartly(*other.node)
        except AttributeError:
            return self._slist.hasItemPartly(*other)

    def append(self, mobj):
        """Adds given object to the list object.
        Append takes one of three objects:
            - maya string object
            - maya component tuple
            - mampy Component object

        NOTE: This function might have to undergo a performance check.
        """
        if isinstance(mobj, basestring):
            mobj = get_component_from_input(mobj)

        if hasattr(mobj, '__iter__'):
            try:
                self._slist.add(mobj, mergeWithExisting=False)
            except TypeError:
                self._slist.add(mobj.node, mergeWithExisting=False)
        else:
            raise TypeError(
                '{} is not a valid {} type.'.
                format(type(mobj), self.__class__.__name__)
            )

    def extend(self, other):
        """
        Generally converting from stringlists should be avoided and one
        should strive to stay in the api as long as possible.
        """
        # Must empty cache as there is no way to check which items are being
        # merged, or  changed during an add or listmerge without too steep
        # performance costs.
        self._cache.clear()
        try:
            self._slist.merge(
                other._slist, strategy=api.MSelectionList.kMergeNormal
            )
        except AttributeError:
            element = iter(other).next()
            if isinstance(element, basestring):
                self._slist.merge(
                    self.__class__(other)._slist,
                    strategy=api.MSelectionList.kMergeNormal
                )
            elif isinstance(element, AbstractComponent):
                for component in other:
                    self._slist.add(component.node)

    def replace(self, index, other):
        if hasattr(other, '__iter__'):
            try:
                self._cache.pop(index, None)
                self._slist.replace(index, other)
            except AttributeError:
                self._cache[index] = other
                self._slist.replace(index, other.node)
        else:
            raise TypeError(
                '{} cant be added to a ComponentList.'.format(type(other))
            )


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

    def _process_dispatcher(self, elements, merge):
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

    def _process_dispatcher(self, elements, merge):
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
            return self.__class__(
                [
                    getattr(self._slist, self._get_func)(i)
                    for i in xrange(*key.indices(len(self)))
                ]
            )
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

    def append(self, other):
        pass

    def extend(self, other):
        pass

    def replace(self, other):
        pass


class DagpathList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(DagpathList, self).__init__(Node, dagpath, merge)


class DependencyList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(DependencyList, self).__init__(DependencyNode, dagpath, merge)


class PlugList(DagbaseList):
    def __init__(self, dagpath=None, merge=True):
        super(PlugList, self).__init__(Plug, dagpath, merge)
