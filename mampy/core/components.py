"""
This module contains the `Component` class and functions for working with
``Component`` objects.
"""
import logging
import itertools
import collections
from abc import ABCMeta

# Maya API import
import maya.cmds as cmds
import maya.api.OpenMaya as api
from maya.api.OpenMaya import MFn

from mampy.core.utils import IndicesDict, ObjectDict, get_average_vert_normal
from mampy.core.datatypes import BoundingBox
from mampy.core.dagnodes import Node


logger = logging.getLogger(__name__)


__all__ = ['SingleIndexComponent', 'MeshVert', 'MeshEdge', 'MeshPolygon', 'MeshMap']


def get_component_from_string(input_string):
    return api.MSelectionList().add(input_string).getComponent(0)


class AbstractComponent(object):
    __metaclass__ = ABCMeta

    _mtype = None
    _indexed_class = None
    _mtype_str = {
        MFn.kMeshVertComponent: 'vtx',
        MFn.kMeshPolygonComponent: 'f',
        MFn.kMeshEdgeComponent: 'e',
        MFn.kMeshVtxFaceComponent: 'vtxFace',
        MFn.kMeshMapComponent: 'map',
    }

    space = api.MSpace.kWorld

    def __new__(cls, dagpath, object=None):
        if not object:
            return super(AbstractComponent, cls).__new__(cls, dagpath)
        else:
            for c in cls.__subclasses__():
                if object.apiType() == c._mtype:
                    return super(AbstractComponent, cls).__new__(c, dagpath, object)
            else:
                return super(AbstractComponent, cls).__new__(cls, dagpath, object)

    def __init__(self, dagpath, mobject):
        self.dagpath = dagpath
        self.mobject = mobject

        self._mesh = None

    @property
    def mesh(self):
        if self._mesh is None:
            self._mesh = api.MFnMesh(self.dagpath)
        return self._mesh

    @property
    def node(self):
        return (self.dagpath, self.mobject)

    @classmethod
    def create(cls, dagpath, comptype=None):
        comptype = comptype or cls._mtype
        if isinstance(dagpath, basestring):
            dagpath = api.MSelectionList().add(dagpath).getDagPath(0)

        indexed = cls._indexed_class()
        indexed = indexed.create(comptype)
        cfn = api.MFnComponent(indexed)
        cfn.setObject(dagpath.node())
        return cls(dagpath, indexed)

    def new(self):
        return self.create(self.dagpath)

    def add(self, indices):
        try:
            self._indexed.addElements(indices)
        except TypeError:
            self._indexed.addElement(indices)
        return self

    def convert_to(self, cls, **kwargs):
        sl = api.MSelectionList()
        for dp in cmds.polyListComponentConversion(self.cmdslist(), **kwargs):
            sl.add(dp)
        return cls(*sl.getComponent(0))

    def cmdslist(self):
        return api.MSelectionList().add(self.node).getSelectionStrings()


class SingleIndexComponent(AbstractComponent):
    _indexed_class = api.MFnSingleIndexedComponent

    def __init__(self, dagpath, mobject=None):
        super(SingleIndexComponent, self).__init__(dagpath, mobject)
        self._indexed = self._indexed_class(self.mobject)

        self.mdag = Node(dagpath)
        self._verts = None
        self._map_shells = {}
        self._mesh_shells = {}

        # For caching different value return depening on which space we are wroking
        # in.
        self._bbox = {}
        self._points = {}
        self._normals = {}

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.mobject is None or self.mobject.isNull():
            return '{}({})'.format(self.__class__.__name__, self.dagpath.partialPathName())
        else:
            return '{}.{}({})'.format(self.dagpath.partialPathName(),
                                      self._mtype_str[self._indexed.componentType],
                                      self.indices)

    def __len__(self):
        try:
            return self._indexed.elementCount
        except RuntimeError:
            return 0

    def __getitem__(self, key):
        return self.new().add(self.indices[key])

    def __iter__(self):
        return iter(self.indices)

    def __eq__(self, other):
        return self._indexed == other._indexed

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        if self.mobject is None or self.mobject.isNull():
            return False
        else:
            return True if len(self) else False

    def __hash__(self):
        return hash(self._indexed)

    def __contains__(self, index):
        return index in self.indices

    @property
    def bbox(self):
        if self.space not in self._bbox:
            pmax = api.MPoint(map(max, itertools.izip(*self.points)))
            pmin = api.MPoint(map(min, itertools.izip(*self.points)))

            bbox = BoundingBox(pmax, pmin)
            if self._mtype == MFn.kMeshMapComponent:
                bbox.boxtype = '2D'
            self._bbox[self.space] = bbox
        return self._bbox[self.space]

    @property
    def index(self):
        return self._indexed.element(0)

    @property
    def indices(self):
        return self._indexed.getElements()

    @property
    def points(self):
        if self.space not in self._points:
            pts = self.mesh.getPoints(self.space)
            if self.type in [MFn.kMeshMapComponent, MFn.kMeshVertComponent]:
                if self.type == MFn.kMeshMapComponent:
                    pts = list(itertools.izip(*self.mesh.getUVs()))
                indices = self.indices
            else:
                indices = self.vertices
            self._points[self.space] = ObjectDict({idx: pts[idx] for idx in indices})
        return self._points[self.space]

    @property
    def normals(self):
        if self._normals is None:
            self._normals = self.mesh.getNormals()
        return self._normals

    @property
    def map_shells(self):
        """
        Shells are represented by a set of vertices.
        """
        if not self._map_shells:
            count, array = self.mesh.getUvShellsIds()
            if self.is_complete():
                wanted = set(list(xrange(count)))
            else:
                wanted = set([array[idx] for idx in self.indices])

            self._map_shells = {idx: self.new() for idx in wanted}
            for idx, element in enumerate(array):
                if element not in wanted:
                    continue
                self._map_shells[element].add(idx)
        return self._map_shells

    @property
    def mesh_shells(self):
        def dfs(control_set, start):
            seen, stack = set(), [start]
            while stack:
                index = stack.pop()
                if index not in seen:
                    shell = cmds.polySelect(str(self.dagpath), q=True, ets=index, ns=True)
                    seen.update(shell)
                    stack.extend(control_set - seen)
                    yield shell

        if not self._mesh_shells:
            faces = self.to_face()
            control_set, start_index = set(faces.indices), faces.indices[0]
            for idx, shell in enumerate(dfs(control_set, start_index)):
                mesh_shell = faces.new().add(shell)
                if not self.type == MFn.kMeshPolygonComponent:
                    mesh_shell = mesh_shell.convert_to(self.type)
                self._mesh_shells[idx] = mesh_shell
        return self._mesh_shells

    @property
    def type(self):
        return self._mtype

    @property
    def typestr(self):
        return self.mobject.apiTypeStr

    def get_complete(self):
        count = {
            MFn.kMeshVertComponent: self.mesh.numVertices,
            MFn.kMeshEdgeComponent: self.mesh.numEdges,
            MFn.kMeshPolygonComponent: self.mesh.numPolygons,
            MFn.kMeshMapComponent: self.mesh.numUVs(),
        }[self.type]
        complete = self.new()
        complete._indexed.setCompleteData(count)
        return self.__class__(self.dagpath, complete.mobject)

    def get_connected_components(self, convert=True):
        """Return connected vertices from self."""
        def get_return_list(node):
            new = MeshVert.create(self.dagpath).add(node)
            if convert:
                if self.type in (MFn.kMeshEdgeComponent,
                                 MFn.kMeshPolygonComponent):
                    new = new.convert_to(self.type, internal=True)
                else:
                    new = new.convert_to(self.type)
            return new

        def connected_vert_indices(component):
            def dfs(node, index):
                taken[index] = True
                while True:
                    updated = False
                    for i, item in enumerate(component):
                        if not taken[i] and not node.isdisjoint(item):
                            taken[i] = updated = True
                            node.update(item)

                    if not updated:
                        return node

            taken = [False] * len(component)
            for i, node in enumerate(component):
                if not taken[i]:
                    yield get_return_list(dfs(node, i))
        # Make sure we are working with edges, edges are the most viable component to
        # try to find connected with.
        component = self
        if not self.type == MFn.kMeshEdgeComponent:
            if self.type in [MFn.kMeshVertComponent, MFn.kMeshMapComponent]:
                component = self.to_edge(internal=True)
            else:
                component = self.to_edge()

        # Sorting the edge indices into shared sets will make the code run six times
        # faster in dfs.
        edge_indices = (component.mesh.getEdgeVertices(e) for e in component.indices)
        index_vert_map = collections.defaultdict(set)
        for edge in edge_indices:
            index_vert_map[edge[0]].update(edge)

        return connected_vert_indices(index_vert_map.values())

    def is_border(self, index):
        """
        Check if component index is on border of mesh.
        """
        if self.type == api.MFn.kMeshPolygonComponent:
            return self.mesh.onBoundary(index)
        elif self.type == api.MFn.kMeshEdgeComponent:
            return cmds.polySelect(self.dagpath, q=True, edgeBorder=index, ns=True) or False
        else:
            edge = self.new().add(index).to_edge()
            return any(
                [cmds.polySelect(self.dagpath, q=True, edgeBorder=i, ns=True) for i in edge.indices]
            )
        return False

    def is_complete(self):
        return {
            MFn.kMeshPolygonComponent: self.mesh.numPolygons,
            MFn.kMeshEdgeComponent: self.mesh.numEdges,
            MFn.kMeshVertComponent: self.mesh.numVertices,
            MFn.kMeshMapComponent: self.mesh.numUVs(),
        }[self.type] == len(self.indices)

    def is_valid(self, comptype=None):
        if comptype is None:
            return not(self.mobject.isNull())
        return self.type == comptype

    def is_face(self):
        """
        Shorthand for ``self.is_valid(MFn.kMeshPolygonComponent)``
        """
        return self.is_valid(MFn.kMeshPolygonComponent)

    def is_edge(self):
        """
        Shorthand for ``self.is_valid(MFn.kMeshEdgeComponent)``
        """
        return self.is_valid(MFn.kMeshEdgeComponent)

    def is_vert(self):
        """
        Shorthand for ``self.is_valid(MFn.kMeshVertComponent)``
        """
        return self.is_valid(MFn.kMeshVertComponent)

    def is_map(self):
        """
        Shorthand for ``self.is_valid(MFn.kMeshMapComponent)``
        """
        return self.is_valid(MFn.kMeshMapComponent)

    def translate(self, **kwargs):
        cmds.xform(self.cmdslist(), **kwargs)

    def to_vert(self, **kwargs):
        return self.convert_to(MFn.kMeshVertComponent, **kwargs)

    def to_edge(self, **kwargs):
        converted = self.convert_to(MFn.kMeshEdgeComponent, **kwargs)
        # When converting to borders from mesh to face, if the face is at mesh
        # border the edges won't be returned. We perform a manual convert
        # and add the missing edges to the converted object.
        if self.is_face() and 'border' in kwargs:
            border_edges = []
            for face in self:
                if self.is_border(face):
                    n_edge = self.new().add(face).to_edge()
                    for idx in n_edge:
                        if n_edge.is_border(idx):
                            border_edges.append(idx)
            converted.add(border_edges)
        return converted

    def to_face(self, **kwargs):
        return self.convert_to(MFn.kMeshPolygonComponent, **kwargs)

    def to_map(self, **kwargs):
        return self.convert_to(MFn.kMeshMapComponent, **kwargs)

    def convert_to(self, comptype, **kwargs):
        cls, kw = {
            MFn.kMeshVertComponent: (MeshVert, {'toVertex': True}),
            MFn.kMeshEdgeComponent: (MeshEdge, {'toEdge': True}),
            MFn.kMeshPolygonComponent: (MeshPolygon, {'toFace': True}),
            MFn.kMeshMapComponent: (MeshMap, {'toUV': True}),
        }[comptype]
        kwargs.update(kw)
        return super(SingleIndexComponent, self).convert_to(cls, **kwargs)

    def toggle(self, other=None):
        if other is None:
            component = self.get_complete()
        else:
            if self.dagpath == other.dagpath:
                component = other
            else:
                return logger.warn('{} is not same component.'.format(other))
        sl = api.MSelectionList().add(self.node)
        sl.toggle(self.dagpath, component.mobject)
        return self.__class__(*sl.getComponent(0))


class MeshVert(SingleIndexComponent):
    _mtype = MFn.kMeshVertComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshVert, cls).create(dagpath, cls._mtype)

    @property
    def normals(self):
        if self.space not in self._normals:
            self._normals[self.space] = self.mesh.getVertexNormals(False, self.space)
        return self._normals[self.space]


def get_border_loop_indices_from_edge_index(index):
    return set(sorted([int(i) for i in cmds.polySelect(q=True, edgeBorder=index)]))


def get_border_loop_indices_from_edge_object(component):
    return set([
        tuple(border for border in get_border_loop_indices_from_edge_index(idx))
        for idx in component.indices
    ])


def get_outer_and_inner_edges_from_edge_loop(loop):
    """
    Return outer edges from a component object containing connected
    edges.
    """
    # Get tuples with vert ids representing edges
    # edges = connected.vertices
    edge_vert_map = loop.vertices
    indices = set(edge_vert_map)

    # Get verts with least occurances
    vert_count = collections.Counter(sum(edge_vert_map.itervalues(), ()))
    outer_verts = set(i[0] for i in vert_count.most_common()[-2:])
    inner_verts = indices - outer_verts

    edge_list = []
    for i in outer_verts:
        edge = MeshVert.create(loop.dagpath)
        for idx, verts in edge_vert_map.viewitems():
            if i in verts:
                edge.add(verts); break
        edge_list.append(edge)
    return edge_list, MeshVert.create(loop.dagpath).add(inner_verts)


def get_vert_order_from_connected_edges(edge_vertices):
    """
    .. note:: Should probably be moved to mampy.
    """
    idx = 0
    next_ = None
    sorted_ = []
    while edge_vertices:

        edge = edge_vertices.pop(idx)
        # next_ is a vert on the edge index.
        if next_ is None:
            next_ = edge[-1]

        sorted_.append(next_)
        for i in edge_vertices:
            if next_ in i:
                idx = edge_vertices.index(i)
                next_ = i[-1] if next_ == i[0] else i[0]
                break
    return sorted_


class MeshEdge(SingleIndexComponent):
    _mtype = MFn.kMeshEdgeComponent

    def __init__(self, dagpath, mobject=None):
        super(MeshEdge, self).__init__(dagpath, mobject)
        self._vert_normals = {}

    @classmethod
    def create(cls, dagpath):
        return super(MeshEdge, cls).create(dagpath, cls._mtype)

    @property
    def normals(self):
        if self.space not in self._normals:
            if self.space not in self.vert_normals:
                self.vert_normals[self.space] = self.mesh.getVertexNormals(False,
                                                                           self.space)

            get_edge_verts = self.mesh.getEdgeVertices
            get_vert_normals = self.vert_normals[self.space]
            self._normals[self.space] = ObjectDict({
                idx: get_average_vert_normal(get_vert_normals, get_edge_verts(idx))
                for idx in self.indices
            })
        return self._normals[self.space]

    @property
    def vertices(self):
        if self._verts is None:
            get_vert = self.mesh.getEdgeVertices
            self._verts = IndicesDict({idx: get_vert(idx) for idx in self.indices})
        return self._verts


class MeshPolygon(SingleIndexComponent):
    _mtype = MFn.kMeshPolygonComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshPolygon, cls).create(dagpath, cls._mtype)

    @property
    def normals(self):
        if not self._normals:
            self._normals = ObjectDict(
                {idx: self.mesh.getPolygonNormal(idx) for idx in self.indices}
            )
        return self._normals

    @property
    def vertices(self):
        if self._verts is None:
            get_vert = self.mesh.getPolygonVertices
            self._verts = IndicesDict({idx: tuple(get_vert(idx)) for idx in self.indices})
        return self._verts


class MeshMap(SingleIndexComponent):
    _mtype = MFn.kMeshMapComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshMap, cls).create(dagpath, cls._mtype)

    def translate(cls, **kwargs):
        cmds.polyEditUV(list(cls), **kwargs)
