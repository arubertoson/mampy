# -*- coding: utf-8 -*-
"""
mampy.core.listadapters

This module contains the ObjectList Adapters that Mampy uses to convert Maya
objects to Mampy objects.
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from functools import total_ordering

from maya import cmds
from maya.api import OpenMaya as om

from mampy.core import cache
from mampy.core.cache import cache_MList_object, invalidate_instance_cache
from mampy.core.components import ComponentFactory, MultiComponent
from mampy.core.exceptions import OrderedSelectionsNotSet
from mampy.core.utils import (
    IMayaStringList, get_maya_strlist_from_iterable, is_track_order_set,
    itermayalist, need_ordered_selection_set, get_maya_component_from_input)

__all__ = ('ComponentList', 'MultiComponentList', 'DagpathList',
           'DependencyNodeList', 'PlugList')


class AbstractMListFactory(object):
    """Implements Factory object to create MSelectionList object from various
    constructors and validate list before use.

    As Maya's MSelectionList can hold all maya objects we have to enforce
    a typecheck to ensure that the objects we are working on are indeed of
    the desired list type.
    """
    __metaclass__ = ABCMeta
    __slots__ = ()

    @classmethod
    def from_selected(cls):
        return cls(om.MGlobal.getActiveSelectionList())

    @classmethod
    def from_strings(cls, string_elements, merge=True):
        return cls(get_maya_strlist_from_iterable(string_elements))

    @classmethod
    def from_ls(cls, *args, **kw):
        """Wraps the cmds.ls command to query objects from the maya scene.

        Merge will be used when we try to query from lists that require it.
        """
        # Assume that we want to merge the selection list
        merge = True
        if need_ordered_selection_set(kw):
            if not is_track_order_set():
                raise OrderedSelectionsNotSet()
            # If we are tracking order we can't merge the components
            merge = False

        if 'merge' in kw:
            merge = kw.pop('merge')
        return cls.from_strings(cmds.ls(*args, **kw), merge)

    def __init__(self, mlist=None):
        self._mlist = self._factory_method(mlist)

    def _factory_method(self, mlist):
        if mlist is not None:
            if mlist.isEmpty():
                return om.MSelectionList().copy(mlist)
            else:
                self._mlist = mlist
                if self.is_valid():
                    return om.MSelectionList().copy(mlist)
                else:
                    raise TypeError(
                        'Given MSelectionList does not contain objects for {}'.
                        format(self.__class__.__name__))
        else:
            return om.MSelectionList()

    @abstractmethod
    def is_valid(self):
        """If there is one item in the list that does not contain any
        valid items the whole list is invalid as __getitem__ won't work
        correctly.
        """
        return False


@total_ordering
class AbstractMListSequence(object):
    """Implements a mutable sequence of a MSelectionList adapter.

    Object will translate a legacy Maya Obejct to a Mampy Object through
    given methods and types after concrete subclass overrides:
    __new__ or __init__, _getitem_method, _getitem_type, __contains__
    and __len__.
    """
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractproperty
    def _getitem_method(self):
        """Represent MSelectionList method to be used when getting elements
        from the list.
        """
        return None

    @abstractproperty
    def _getitem_type(self):
        """Represents the class object to be used when creating new objects
        to return.
        """
        return None

    @abstractmethod
    def __len__(self):
        return 0

    @abstractmethod
    def __contains__(self, mobject):
        return False

    def __eq__(self, other):
        if len(self) == len(other):
            return all(
                self.__contains__(self._getitem_method(obj))
                for obj in xrange(len(other)))
        return False

    def __lt__(self, other):
        return len(self) < len(other)

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]

    def __reversed__(self):
        for i in reversed(xrange(len(self))):
            yield self[i]

    def _slice_list(self, key):
        sliced = om.MSelectionList()
        for i in xrange(*key.indices(len(self))):
            sliced.add(self._getitem_method(i))
        return self.__class__(sliced)

    def __getitem__(self, key):
        try:
            return self._slice_list(key)
        except AttributeError:
            return self._getitem_type(self._getitem_method(key))


class AbstractMListAdapter(AbstractMListFactory, AbstractMListSequence,
                           IMayaStringList):
    """Provides adapter for Maya API MSelectionList object.

    Class provides a concrete adapter to MSelectionList -> python list object,
    must implement __new__ or __init__ and __getitem__ to provide
    the MSelectionList object.
    """
    __metaclass__ = ABCMeta
    __slots__ = ()

    def __len__(self):
        return self._mlist.length()

    def __str__(self):
        return str(self._mlist)

    def __hash__(self):
        return self._mlist.__hash__()

    def __nonzero__(self):
        return not (self._mlist.isEmpty())

    def __copy__(self):
        return self.__class__(om.MSelectionList().copy(self._mlist))

    def __setitem__(self, index, value):
        self._mlist.replace(index, value)

    def append(self, obj):
        """Appends a maya object to the end of the list."""
        self._mlist.add(obj, mergeWithExisting=False)

    def extend(self, objs):
        """Extend list object with maya objects."""
        for obj in objs:
            self.append(obj)

    def pop(self, index=-1):
        index = len(self) - 1 if index == -1 else index
        value = self[index]
        self.remove(index)
        return value

    __delitem__ = pop

    def remove(self, index):
        return self._mlist.remove(index)

    def cmdslist(self, index=None):
        if index:
            return self._mlist.getSelectionStrings(index)
        return self._mlist.getSelectionStrings()


class CacheableMListAdapter(AbstractMListAdapter):
    """Attempts to cache objects returned from __getitem__ for future use,
    discards objects upon removal or update of MListSequence.

    This class provides concrete generic base template for behaviour of a
    cached python list except for: is_valid, _getitem_mehtod, _getitem_type
    and __contains__.
    """
    __metaclass__ = ABCMeta
    __slots__ = ()

    @cache_MList_object
    def __getitem__(self, key):
        return super(CacheableMListAdapter, self).__getitem__(key)

    @cache_MList_object(action=cache.COPY)
    def __copy__(self):
        return super(CacheableMListAdapter, self).__copy__()

    @cache_MList_object(action=cache.POP)
    def __setitem__(self, index, value):
        super(CacheableMListAdapter, self).__setitem__(index, value)

    @cache_MList_object(action=cache.POP)
    def remove(self, index):
        super(CacheableMListAdapter, self).remove(index)


class ComponentList(CacheableMListAdapter):
    """ComponentList is a container for Maya Components.

    A Component Object in Maya is a MObject containing different types of
    component indices. A (DagPath, MObject) creates a component bound to a
    DagPath object.

    There is an extra method that should be highlighted in the ComponentList
    object, as indices and different types all are Contained within the same
    MObject is often prefered to use the update method to add objects to the
    ComponentList. Unless you want duplicated Components in the list, append
    will just add the component object to the end of the list where update will
    try to update existing objects in the list. its important to differiatiate
    between the two.
    """
    __slots__ = ('_mlist', '_cache')

    def __contains__(self, component):
        return self._mlist.hasItemPartly(*component)

    @classmethod
    def from_strings(cls, string_elements, merge=True):
        mlist = om.MSelectionList()
        for each in string_elements:
            # Need to convert the string to a component object before adding,
            # else it will merge normally weather we want it or not.
            comp = get_maya_component_from_input(each)
            mlist.add(comp, mergeWithExisting=merge)
        return cls(mlist)

    @property
    def _getitem_type(self):
        return ComponentFactory

    @property
    def _getitem_method(self):
        return self._mlist.getComponent

    def is_valid(self):
        for each in itermayalist(self._mlist):
            if not each.hasComponents():
                return False
        else:
            return True

    @invalidate_instance_cache
    def update(self, other):
        """Update will try to update existing Component Objects in the list,
        if none are found will instead add to the list.

        Seeing as any object in the list can be updated without any direct or
        easy way to check we have to invalidate the whole cache.
        """
        try:
            self._mlist.merge(
                other._mlist, strategy=om.MSelectionList.kMergeNormal)
        except AttributeError:
            self._mlist.add(other)


class MultiComponentList(ComponentList):
    """MultiComponentList for handling Multiple types of Maya Components.

    NOTE: Incomplete Docstring

    A Multi Component is a DagPath connected with multiple MObjects types. To
    work with multicomponents we create a MultiComponent containing the various
    component types and return it as the list item. Meaning one should not
    operate on the returned object from a multicomponent list but iterate over
    it again to get a usable Mampy Component object.

    As stated in the Appendix D: API and Developer Kit limitations we have to
    use the MItSelectionList to work with multiple types of object components.

    An alternative is to call getSelectionStrings and create a new
    MSelectionList, it is, however, really slow.
    """
    __slots__ = ('_mlist', '_cache')

    def _get_first_itercomp(self, index):
        return self._mlist.getComponent(index)

    def _get_last_itercomp(self, index):
        try:
            res = self._mlist.getComponent(index + 1)
        except IndexError:
            res = om.MObject()
        return res

    def _get_iterstart(self, start):
        iterator = om.MItSelectionList(self._mlist)
        dag, startcomp = start[0], om.MFnComponent(start[1])
        while not iterator.isDone():
            comp = iterator.getComponent()
            if dag == comp[0] and startcomp.isEqual(comp[1]):
                return iterator
            iterator.next()
        raise IndexError('Invalid Index in MSelectionList')

    def _get_multilist_till_last(self, iterator, last):
        multilist = om.MSelectionList()
        dag, lastcomp = last[0], om.MFnComponent(last[1])
        while not iterator.isDone():
            comp = iterator.getComponent()
            if dag == comp[0] and lastcomp.isEqual(comp[1]):
                break
            multilist.add(comp, mergeWithExisting=False)
            iterator.next()
        return multilist

    def _get_multilist_from_index(self, key):
        firstcomp = self._get_first_itercomp(key)
        lastcomp = self._get_last_itercomp(key)

        mlistiter = self._get_iterstart(firstcomp)
        return self._get_multilist_till_last(mlistiter, lastcomp)

    @property
    def _getitem_method(self):
        return self._get_multilist_from_index

    @property
    def _getitem_type(self):
        return MultiComponent


class AbstractObjectBase(CacheableMListAdapter):
    """Implements generic methods for Maya Dag objects."""
    __slots__ = ()

    @classmethod
    def from_name(cls, pattern):
        return cls(om.MGlobal.getSelectionListByName(pattern))

    def __contains__(self, node):
        return self._mlist.hasItem(node)


class DagpathList(AbstractObjectBase):
    """DagpathList is a container for Maya MDagPath objects."""
    __slots__ = ('_mlist', '_cache')

    @property
    def _getitem_method(self):
        return self._mlist.getDagPath

    @property
    def _getitem_type(self):
        return Dagpath

    def is_valid(self):
        for each in itermayalist(self._mlist):
            try:
                each.getDagPath()
            except RuntimeError:
                return False
        return True


class DependencyNodeList(AbstractObjectBase):
    """DependencyNodeList is a container for Maya MFnDependencyNode objects."""
    __slots__ = ('_mlist', '_cache')

    @property
    def _getitem_method(self):
        return self._mlist.getDependNode

    @property
    def _getitem_type(self):
        return DependencyNode

    def is_valid(self):
        for each in itermayalist(self._mlist):
            try:
                each.getDependNode()
            except RuntimeError:
                return False
        return True


class PlugList(AbstractObjectBase):
    """PlugList is a container for Maya MPlug objects."""
    __slots__ = ('_mlist', '_cache')

    @property
    def _getitem_method(self):
        return self._mlist.getPlug

    @property
    def _getitem_type(self):
        return Plug

    def is_valid(self):
        for each in itermayalist(self._mlist):
            try:
                each.getPlug()
            except RuntimeError:
                return False
        return True
