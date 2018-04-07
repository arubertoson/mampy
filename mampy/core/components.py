# -*- coding: utf-8 -*-
"""
mampy.core.components

This modules contains the various Mampy Components.
"""
from abc import ABCMeta, abstractmethod, abstractproperty

from maya.api import OpenMaya as om

from mampy.core import cache, compiterators, utils
from mampy.core.datatypes import IndexValueMap
from mampy.core.cache import (cached_property, memoize_property, memoize,
                              invalidate_instance_cache)


# def get_component_count_from_mampy_component(comp):
#     return {
#         om.MFn.kMeshVertComponent: comp.mesh.numVertices,
#         om.MFn.kMeshEdgeComponent: comp.mesh.numEdges,
#         om.MFn.kMeshPolygonComponent: comp.mesh.numPolygons,
#         om.MFn.kMeshMapComponent: comp.mesh.numUVs(),
#     }[comptype]


def get_bounding_box_from_points(it):
    return om.MBoundingBox(om.MPoint(map(min, it)), om.MPoint(map(max, it)))


def get_indexed_from_cls(cls):
    indexed = cls._mfn_indexed()
    compobj = indexed.create(cls._mfn_type)
    return indexed, compobj


class AbstractIndexed(object):
    """Indexed is a container for component indices.

    A Indexed object is a abstract class defining functionality for
    working with indexed objects.

    Many of the methods that retrieve information can be quite heavy depending
    on the amount of contained indices. We should aim to memoize these
    methods while retaining the ability to reset the cache when the object
    changes.
    """

    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractproperty
    def _mfn_indexed(self):
        return None

    @abstractproperty
    def indexed(self):
        """Can only be implemented when the class knows which indexed type to
        use and the arguments that specific class takes.
        """
        return None

    @memoize_property
    def indices(self):
        """Sets are easier to work with when working with more than one indexed
        object, caclulation difference, union, intersection is made easy with
        sets and well worth the overhead to change the list object.
        """
        return set(self.indexed().getElements())

    @memoize_property
    def elements(self):
        return self.indexed().getElements()

    @abstractmethod
    def setcomplete(self, num):
        return self.indexed.setCompleteData(num)

    def __eq__(self, other):
        return self.indexed.isEqual(other)

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __nonzero__(self):
        """A MFn indexed component class can exists without a valid component
        object making it vulnerable to invalid nonzero checks. To remedy this
        we first try to do it the right way. If that doesn't work double check
        with the base object.
        """
        try:
            return not (self.indexed.isEmpty)
        except RuntimeError:
            return not (self.indexed.object().isNull())

    def __len__(self):
        return self.indexed.elementCount

    def __hash__(self):
        return hash(self.indexed)

    def __contains__(self, index):
        return index in self.indexed.getElements()

    def __add__(self, other):
        self.add(other.getElements())
        return self._mfn_indexed(self)

    def __radd__(self, other):
        self.add(other.getElements())
        return self

    def is_complete(self):
        return self.indexed.getCompleteData() != 0

    @invalidate_instance_cache
    def add_elements(self, indices):
        """We need to invalidate the caches for the given instance when adding
        new information to it.
        """
        try:
            self.indexed.addElements(indices)
        except TypeError:
            self.indexed.addElement(indices)

    @cached_property
    def type(self):
        return self.indexed.type()


class AbstractComponent(object):
    """Abstract Component is a collection of methods that can be used to
    collect information on the indices of a maya component.
    """
    __metaclass__ = ABCMeta

    def __init__(self, dagpath, mobject):
        self.dagpath = dagpath
        self.object = mobject

    @abstractproperty
    def _mfn_type(self):
        return None

    @abstractmethod
    def points(self, space):
        return None

    @abstractmethod
    def boundingbox(self, space):
        return None

    @abstractmethod
    def normals(self, space):
        return None

    @cached_property
    def mesh(self):
        return om.MFnMesh(self.dagpath)


class SingleIndexedComponent(AbstractComponent, AbstractIndexed):
    """A SingleIndexedComponent is a component represented by a single
    index number.

    In Maya this is vertices, edges, faces and uvs.
    """

    @cached_property
    def _mfn_indexed(self):
        return om.MFnSingleIndexedComponent

    @classmethod
    def from_dagpath(cls, dagpath):
        if isinstance(dagpath, basestring):
            dagpath = utils.get_maya_dagpath_from_input(dagpath)

        _, compobj = utils.get_indexed_from_cls(cls)
        return cls(dagpath, compobj)

    def __getitem__(self, key):
        it = iter(self).next()
        it.setIndex(key)
        return it

    def __eq__(self, other):
        if self.dagpath == other.dagpath:
            return self.indexed == other.indexed
        else:
            return False

    @cached_property
    def indexed(self):
        return self._mfn_indexed(self.dagpath, self.object)


class MeshVertIterator(om.MItMeshVertex):
    """Workaround for bug in python api

    Calling index() after using setIndex will cause RuntimeError.
    """

    def setIndex(self, key):
        self.__index = key
        super(MeshVertIterator, self).setIndex(key)

    def index(self):
        try:
            return self.index()
        except RuntimeError:
            return self.__index


class MeshVert(SingleIndexedComponent):
    """
    """
    _mfn_type = om.MFn.kMeshVertComponent

    def __iter__(self):
        return iter(MeshVertIterator(self.dagpath, self.object))

    @memoize
    def points(self, space=om.MSpace.kWorld):
        points = self.mesh.getPoints(space)
        return IndexValueMap({idx: points[idx] for idx in self.indices})

    @memoize
    def boundingbox(self, space=om.MSpace.kWorld):
        return get_bounding_box_from_points(self.points(space))

    @memoize
    def normals(self, space=om.MSpace.kWorld):
        return None

    def set_complete(self):
        return self.indexed.setCompleteData(self.mesh.numVertices)

    def is_complete(self):
        iscomplete = super(MeshVert, self).is_complete()
        if not iscomplete:
            iscomplete = self.mesh.numVertices == len(self.indices)


class MultiComponent(object):

    def __init__(self, mlist):
        self.mlist = mlist

    def __len__(self):
        return self.mlist.length()


def ComponentFactory(maya_component):
    dag, obj = maya_component
    for each in AbstractComponent.__subclasses__():
        if each._mfn_type == obj.apiType():
            return each(dag, obj)
    else:
        raise TypeError('{} is not a valid maya object'.format(obj.apiTypeStr))
