# -*- coding: utf-8 -*-
"""
mampy.core.sequences

This module contains the list Adapters that Mampy uses to convert Maya
objects to Mampy objects.
"""
import abc
import functools

from maya import cmds
from maya.api import OpenMaya as om

from mampy.core import utils
from mampy.core.exceptions import OrderedSelectionsNotSet


class AbstractMListFactory(object):
    """Implements Factory object to create MSelectionList for use in various
    sequence objects.

    As Maya's MSelectionList can hold all maya objects we have to enforce
    a typecheck to ensure that the objects we are working on are indeed of
    the desired list type.
    """
    __metaclass__ = abc.ABCMeta
    __slots__ = ()

    @classmethod
    def from_selected(cls):
        """Generates a MList object from selections in current maya session."""
        return cls(om.MGlobal.getActiveSelectionList())

    @classmethod
    def from_strings(cls, string_elements, merge=False):
        """Generates a MList object from a sequence of Maya string objects."""
        return cls(utils.get_maya_strlist_from_iterable(string_elements, merge))

    @classmethod
    def from_ls(cls, *args, **kw):
        """Wraps the cmds.ls command to query objects from the maya scene.

        Merge will be used when we try to query from lists that require it.
        """
        # Assume that we want to merge the selection list
        merge = True
        if utils.need_ordered_selection_set(kw):
            if not utils.is_track_order_set():
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

    @abc.abstractmethod
    def is_valid(self):
        """If there is one item in the list that does not contain any
        valid items the whole list is invalid as __getitem__ won't work
        correctly.
        """
        return False


@functools.total_ordering
class AbstractMListSequence(object):
    """Implements a mutable sequence of a MSelectionList adapter.

    Object will translate a legacy Maya Obejct to a Mampy Object through
    given methods and types after concrete subclass overrides:
    __new__ or __init__, _getitem_method, _getitem_type, __contains__
    and __len__.
    """
    __metaclass__ = abc.ABCMeta
    __slots__ = ()

    def __init__(self, mlist):
        self._mlist = mlist

    @abc.abstractproperty
    def _getitem_method(self):
        """Represent MSelectionList method to be used when getting elements
        from the list.
        """

    @abc.abstractproperty
    def _getitem_type(self):
        """Represents the class object to be used when creating new objects
        to return.
        """

    @abc.abstractmethod
    def __contains__(self, mobject):
        """Depending on objects in list there are different ways to check
        contains.
        """

    def __str__(self):
        return str(self._mlist)

    def __len__(self):
        return self._mlist.length()

    def __hash__(self):
        return self._mlist.__hash__()

    def __nonzero__(self):
        return not self._mlist.isEmpty()

    def __copy__(self):
        return self.__class__(om.MSelectionList().copy(self._mlist))

    def __setitem__(self, index, value):
        self._mlist.replace(index, value)

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

    def append(self, obj):
        """Appends a maya object to the end of the list."""
        self._mlist.add(obj, mergeWithExisting=False)

    def extend(self, objs):
        """Extend list object with maya objects."""
        for obj in objs:
            self.append(obj)

    def pop(self, index=-1):
        """Pop last element in list if no index is given else given index."""
        index = len(self) - 1 if index == -1 else index
        value = self[index]
        self.remove(index)
        return value

    __delitem__ = pop

    def remove(self, index):
        """Remove element from list and rebuild indices."""
        return self._mlist.remove(index)

    def cmdslist(self, index=None):
        """Outputs list as a tuple of Maya string objects."""
        if index:
            return self._mlist.getSelectionStrings(index)
        return self._mlist.getSelectionStrings()


class ComponentMListFactory(AbstractMListFactory):
    """Factory generates ComponentList objects."""

    @classmethod
    def from_strings(cls, string_elements, merge=True):
        """Generates MList from string elements.

        We require to convert the Maya Component object before adding to
        MSelectionList to make merge available to us, otherwise MSelectionList
        will merge weather we want it to or not.
        """
        mlist = om.MSelectionList()
        for each in string_elements:
            comp = utils.get_maya_component_from_input(each)
            mlist.add(comp, mergeWithExisting=merge)
        return cls(mlist)

    def is_valid(self):
        for each in utils.itermayalist(self._mlist):
            if not each.hasComponents():
                return False
        return True


class ComponentFactory(object):
    def __init__(self, *args, **kw):
        pass


@cache.CachableSequence
class ComponentList(ComponentMListFactory, AbstractMListSequence):
    """ComponentList is a container for Maya Component objects.

    A component object in Maya is a index list bound to a MDagPath object
    internally represented as a node: (MDagPath, MObject). We don't need to
    track anything in this list as we can delegate that to the Mampy
    `Component` classes, this class only represents an interface between the
    internal maya object and the mampy object.

    As indices and different types all are Contained within the same MObject it
    is often prefered to use the `update` method as it will try to add indices
    to existing components which is usually the desired behaviour. Append will
    function as promised and add a new object to the back of the list.
    """
    __slots__ = ('_mlist', '_cache')

    def __contains__(self, component):
        return self._mlist.hasItemPartly(*component)

    @property
    def _getitem_type(self):
        return ComponentFactory

    @property
    def _getitem_method(self):
        return self._mlist.getComponent

    @cache.invalidate_instance_cache
    def update(self, other):
        """Update will try to update existing Component Objects in the list,
        if none are found will instead append to the list.

        On successful update we will have to reevvaluate the cache as there is
        no sane way of knowing whihc object was modified.
        """
        try:
            self._mlist.merge(
                other._mlist, strategy=om.MSelectionList.kMergeNormal)
        except AttributeError:
            self._mlist.add(other)

