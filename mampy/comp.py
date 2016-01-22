"""
This module contains the `Component` class and functions for working with
``Component`` objects.
"""

import logging
import itertools
import collections

# Maya API import
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.api.OpenMaya as api
from maya.api.OpenMaya import MFn

from mampy.datatypes import BoundingBox


logger = logging.getLogger(__name__)

__all__ = ['Component', 'MeshVert', 'MeshEdge', 'MeshPolygon', 'MeshMap',
           'get_outer_edges_in_loop', 'get_connected_components_in_comp']


# def get_connected_components_on_object(comp):
#     """
#     Loop through given indices and check if they are connected. Maps
#     connected indices and returns a dict.

#     This one utilizes the get_connected in class. It's around 10 times slower
#     than the function below, so for now... It's redundant.

#     """
#     def is_index_connected(index):
#         return any(
#             c in connected[connected_set_count]
#             for c in comp.get_connected(index)
#             )

#     connected_set_count = 0
#     indices = set(comp.indices)
#     connected = collections.defaultdict(set)
#     while indices:

#         connected_set_count += 1
#         connected[connected_set_count].add(indices.pop())
#         while True:
#             is_connected = False

#             for i in indices.copy():
#                 if is_index_connected(i):
#                     is_connected = True
#                     connected[connected_set_count].add(i)
#                     indices.remove(i)
#             if not is_connected:
#                 break
#     return connected


def get_outer_edges_in_loop(connected):
    """
    Return outer edges from a component object containing connected
    edges.
    """
    # Get tuples with vert ids representing edges
    edges = [connected.mesh.getEdgeVertices(i) for i in connected.indices]
    indices = set(sum(edges, ()))

    # Create a counter and count vert ids
    vert_count = collections.Counter()
    vert_count.update(i for e in edges for i in e)

    # Edges are represented as a tuple containing MeshVerts. This is
    # so in case of vector creation you will get the right direction.
    outer_edges = []
    for each in vert_count.most_common()[-2:]:

        outer_vert = each[0]
        outer_edge = [e for e in edges if outer_vert in e].pop()
        inner_vert = [v for v in outer_edge if not outer_vert == v].pop()
        indices.remove(outer_vert)

        outer_edges.append(tuple(
            MeshVert.create(str(connected.dagpath)).add(i)
            for i in [outer_vert, inner_vert]
            ))
    dag = str(connected.dagpath)
    return outer_edges, MeshVert.create(dag).add(indices)


def get_connected_components_in_comp(comp, convert_to_origin_type=True):
    """
    Loop through given indices and check if they are connected. Maps
    connected indices and returns a dict.

    .. todo: rewrite if / elif segments to something a bit more pleasing to
            the eyes
    """
    def is_ids_in_loop(ids):
        """
        Check if id is connected to any indices currently in
        connected[connected_set_count] key.
        """
        id1, id2 = ids
        for edge in connected[connected_set_count]:
            if id1 in edge or id2 in edge:
                return True
        return False

    def get_return_list():
        """
        Create return list containing connected components.
        """
        # Create list and append connected comps as list object.
        return_list = []
        for i in connected.itervalues():
            return_comp = MeshVert.create(comp.dagpath)
            return_comp.add(set(sum(i, ())))
            if comp.type in [api.MFn.kMeshEdgeComponent,
                             api.MFn.kMeshPolygonComponent]:
                converted = return_comp.convert_to(comp.type, internal=True)
            else:
                converted = return_comp.convert_to(comp.type)
            return_list.append(converted)
        return return_list

    # Needs to make sure that edges does not extend outside of the
    # selection border.
    if comp.type == api.MFn.kMeshEdgeComponent:
        edge = comp
    elif comp.type in [api.MFn.kMeshVertComponent,
                       api.MFn.kMeshMapComponent]:
        edge = comp.to_edge(internal=True)
    else:
        edge = comp.to_edge()

    # Set up necessary variables
    connected_set_count = 0
    connected = collections.defaultdict(set)
    indices = set([edge.mesh.getEdgeVertices(e) for e in edge.indices])
    while indices:

        connected_set_count += 1
        connected[connected_set_count].add(indices.pop())

        # Map connected until no match can be found
        while True:
            loop_growing = False
            for ids in indices.copy():
                if is_ids_in_loop(ids):
                    loop_growing = True
                    connected[connected_set_count].add(ids)
                    indices.remove(ids)
            if not loop_growing:
                break

    return get_return_list()


class Component(object):
    """
    A base component class, providing most behavior that other component
    classes can inherit and override, as necessary.

    :param dagpath: dagpath str, list of dagpath str or
                    ``api.OpenMaya.MDagPath``
    :param compobj: ``api.OpenMaya.MObject``

    Usage::

        >>> import mampy
        >>> comp = mampy.Component('pCube1.f[0]')
        MeshPolygon('pCube1.f[0]')

    .. note:: :class:`Component` does not yet support vertex faces.
    """
    __mtype__ = None

    TYPESTR = {
        MFn.kMeshVertComponent: 'vtx',
        MFn.kMeshPolygonComponent: 'f',
        MFn.kMeshEdgeComponent: 'e',
        MFn.kMeshVtxFaceComponent: 'vtxFace',
        MFn.kMeshMapComponent: 'map',
    }

    def __new__(cls, dagpath, compobj=None):
        # If class is not called with MDagPath or MObject creates new MDagPath
        # and MObject from either string list or a string.
        if not (isinstance(dagpath, api.MDagPath) and
                isinstance(compobj, api.MObject)):
            slist = api.MSelectionList()
            if isinstance(dagpath, (list, tuple, set)):
                for i in dagpath:
                    slist.add(i)
            else:
                slist.add(dagpath)

            if slist.length() > 1:
                raise TypeError('More than one object in dagpath.')
            dagpath, compobj = slist.getComponent(0)

        # Fetch right type class
        for c in cls.__subclasses__():
            if not compobj.apiType() == c.__mtype__:
                continue
            cls = c

        self = object.__new__(cls)
        self.__init(dagpath, compobj)
        return self

    def __init(self, dagpath, compobj):
        self.dagpath = dagpath
        self.object = compobj
        self.space = api.MSpace.kWorld

        self._slist = api.MSelectionList()
        self._slist.add((self.dagpath, self.object))

        self._indexed = api.MFnSingleIndexedComponent(self.object)
        self._bbox = None
        self._mesh = None
        self._points = None
        self._normals = None

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.object.isNull():
            r = '{}'.format(str(self.dagpath))
        elif self._indexed.isEmpty:
            r = '{}.{}[]'.format(self.dagpath, self.TYPESTR[self.type])
        elif len(self) == 1:
            r = self._slist.getSelectionStrings()[0]
        else:
            r = list(self._slist.getSelectionStrings())
        return '{}'.format(r)

    def __len__(self):
        try:
            return self._indexed.elementCount
        except RuntimeError:
            return 0

    def __getitem__(self, index):
        return self.new().add(self.indices[index])

    def __iter__(self):
        return iter(self._slist.getSelectionStrings())

    def __eq__(self, other):
        return self._indexed == other._indexed

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.is_valid()

    def __hash__(self):
        return hash(self._indexed)

    def __contains__(self, other):
        return self._slist.hasItemPartly(other.node)

    @property
    def bounding_box(self):
        """
        Construct a ``api.OpenMaya.MBoundingBox`` object amd return it.

        :rtype: ``api.OpenMaya.MBoundingBox``
        """
        if self._bbox is None:
            pmax = api.MPoint(map(max, itertools.izip(*self.points)))
            pmin = api.MPoint(map(min, itertools.izip(*self.points)))

            self._bbox = BoundingBox(pmax, pmin)
            if self.__mtype__ == MFn.kMeshMapComponent:
                self._bbox.boxtype = '2D'
        return self._bbox

    @property
    def index(self):
        """
        Return first index position in indices or index of component.

        :rtype: ``int``
        """
        try:
            return self._indexed.getElements()[0]
        except IndexError:
            raise IndexError('{} is empty.'.format(self.__class__))

    @property
    def indices(self):
        """
        Return int array of current ``Component`` object.

        :rtype: ``api.OpenMaya.MIntArray``
        """
        return self._indexed.getElements()

    @property
    def node(self):
        """
        Return the `OpenMaya` representation of a component.

        :rtype: ``(api.OpenMaya.MDagPath, api.OpenMaya.MObject)``
        """
        return (self.dagpath, self.object)

    @property
    def mesh(self):
        """
        Construct the ``api.OpenMaya.MFnMesh`` of current component and return
        it.

        :rtype: ``api.OpenMaya.MFnMesh``
        """
        if self._mesh is None:
            self._mesh = api.MFnMesh(self.dagpath)
        return self._mesh

    @property
    def points(self):
        """
        Construct a list of component positions as ``api.OpenMaya.MPoint``
        objects and return it.

        :rtype: ``list``

        .. todo:: Make sure that points represent indices position of
            component object.
        """
        if self._points is None:
            if self.type == MFn.kMeshMapComponent:
                self._points = zip(*self.mesh.getUVs())
                if not self._indexed.isComplete:
                    self._points = [api.MPoint(self._points[idx])
                                    for idx in self.indices]
                    return self._points
            else:
                self._points = self.mesh.getPoints(self.space)
                if not self.__mtype__ == MFn.kMeshVertComponent:
                    if self.__mtype__ == MFn.kMeshEdgeComponent:
                        verts = self.mesh.getEdgeVertices
                    else:
                        verts = self.mesh.getPolygonVertices
                    indices = set(i for idx in self.indices
                                  for i in verts(idx))
                else:
                    indices = self.indices

            if not self._indexed.isComplete:
                    self._points = [self._points[idx] for idx in indices]
        return self._points

    @property
    def type(self):
        """
        :rtype: ``int``
        """
        return self.__mtype__

    @property
    def typestr(self):
        """
        :rtype: ``str``
        """
        return self.object.apiTypeStr

    @classmethod
    def create(cls, dagpath, comptype=None):
        """
        Construct empty :class:`Component` attached to dagpath and return it.

        :param dagpath: str(dagpath), api.OpenMaya.MDagPath
        :param comptype: integer
        :rtype: :class:`Component`

        Usage::

            >>> dagpath = 'pCube1'
            >>> component = Component.create(dagpath, MFn.kMeshVertComponent)
            MeshVert(pCube1.vtx[])
        """
        comptype = comptype or cls.__mtype__
        if isinstance(dagpath, basestring):
            tmp = api.MSelectionList()
            tmp.add(dagpath)
            dagpath = tmp.getDagPath(0)

        indexed = api.MFnSingleIndexedComponent()
        cobj = indexed.create(comptype)
        cfn = api.MFnComponent(cobj)
        cfn.setObject(dagpath.node())
        return cls(dagpath, cobj)

    def new(self):
        return self.create(self.dagpath)

    def add(self, indices):
        """
        Add given index or list of indices to current :class:`Component`
        object.

        :param indices: ``int``, ``sequence``
        """
        if hasattr(indices, '__len__'):
            self._indexed.addElements(indices)
        else:
            self._indexed.addElement(indices)
        self._slist.add(self.node)
        return self

    def to_face(self, **kwargs):
        """
        Shothand for ``self.convert_to(toFace=True)``
        """
        return self.convert_to(MFn.kMeshPolygonComponent, **kwargs)

    def to_edge(self, **kwargs):
        """
        Shothand for ``self.convert_to(toEdge=True)``
        """
        return self.convert_to(MFn.kMeshEdgeComponent, **kwargs)

    def to_vert(self, **kwargs):
        """
        Shothand for ``self.convert_to(toVert=True)``
        """
        return self.convert_to(MFn.kMeshVertComponent, **kwargs)

    def to_map(self, **kwargs):
        """
        Shothand for ``self.convert_to(toUV=True)``
        """
        return self.convert_to(MFn.kMeshMapComponent, **kwargs)

    def convert_to(self, comptype, **kwargs):
        """
        Convert current component to given component type and return it.

        :rtype: :class:`Component`

        .. note:: for some reason converting from map to vertex with
            "border" argument will yield no result with
            polyListComponentConversion.
        """
        if comptype == MFn.kMeshPolygonComponent:
            kwargs.update(toFace=True)
        elif comptype == MFn.kMeshEdgeComponent:
            kwargs.update(toEdge=True)
        elif comptype == MFn.kMeshVertComponent:
            kwargs.update(toVertex=True)
        elif comptype == MFn.kMeshMapComponent:
            kwargs.update(toUV=True)

        s = api.MSelectionList()
        for dp in cmds.polyListComponentConversion(list(self), **kwargs):
            s.add(dp)

        if s.isEmpty():
            logger.warn(
                'Failed to convert {} with keywords: {}'
                .format(list(self), kwargs)
            )
        return Component(*s.getComponent(0))

    def get_complete(self):
        """
        Construct complete component and return it.

        :rtype: :class:`Component`
        """
        if self.type == MFn.kMeshPolygonComponent:
            count = self.mesh.numPolygons
        elif self.type == MFn.kMeshEdgeComponent:
            count = self.mesh.numEdges
        elif self.type == MFn.kMeshVertComponent:
            count = self.mesh.numVertices
        elif self.type == MFn.kMeshMapComponent:
            count = self.mesh.numUVs()

        complete = self.create(self.dagpath)
        complete._indexed.setCompleteData(count)
        return self.__class__(self.dagpath, complete.object)

    def get_connected(self, index, comp_type=None):
        """
        Construct a int array of connected component indices from given index.

        :rtype: `MIntArray`

        .. note:: Temporary method until api 2.0 get a similar feature.
            This is slow and there are better alternativs. use as last
            resort.
        """
        # Create dagpath
        dag_path = om.MDagPath()
        s = om.MSelectionList()
        s.add(str(self.dagpath))
        s.getDagPath(0, dag_path)

        # Create component
        component_index = om.MFnSingleIndexedComponent()
        component = component_index.create(self.__mtype__)
        component_index.addElement(index)

        # Get component
        s = om.MSelectionList()
        s.add(dag_path, component)
        s.getDagPath(0, dag_path, component)

        # Find connected components
        connected = om.MIntArray()
        iterator = {
            MFn.kMeshVertComponent: om.MItMeshVertex,
            MFn.kMeshEdgeComponent: om.MItMeshEdge,
            MFn.kMeshPolygonComponent: om.MItMeshPolygon,
        }[self.__mtype__]
        to_type = {
            MFn.kMeshVertComponent: 'getConnectedVertices',
            MFn.kMeshEdgeComponent: 'getConnectedEdges',
            MFn.kMeshPolygonComponent: 'getConnectedFaces',
        }[comp_type or self.__mtype__]

        iterator = iterator(dag_path, component)
        getattr(iterator, to_type)(connected)
        return connected

    def get_mesh_shell(self):
        """
        Extend current :class:`Component` to contained mesh shell and return
        new :class:`Component`.

        :rtype: :class:`Component`
        """
        faces = self.to_face()
        shell = set()
        for idx in faces.indices:
            if idx in shell:
                continue
            shell.update(
                cmds.polySelect(str(self.dagpath), q=True, ets=idx, ns=True)
            )
        faces.add(shell)
        return faces.convert_to(self.type)

    def __mesh_normals(self, space, angle_weighted):
        if self.type == MFn.kMeshPolygonComponent:
            # Bit unsure which is best method for getting face normal
            # self._normals = self.mesh.getFaceVertexNormals(space)
            self._normals = self.mesh.getNormals(space)
        elif (self.type in [
                MFn.kMeshVertComponent,
                MFn.kMeshEdgeComponent]):
            self._normals = self.mesh.getVertexNormals(angle_weighted, space)

    def get_normal(self, idx, space=api.MSpace.kWorld, angle_weighted=False):
        """
        Place list of normals for correct component type and return depening
        on type.
        """
        if self._normals is None:
            self.__mesh_normals(space, angle_weighted)

        if self.type == MFn.kMeshEdgeComponent:
            v1, v2 = self.mesh.getEdgeVertices(idx)
            return (self._normals[v1]+self._normals[v1]) * 0.5

        elif self.type == MFn.kMeshPolygonComponent:
            face_ids = self.mesh.getFaceNormalIds(idx)
            average = api.MFloatVector()
            for i in face_ids:
                average += self._normals[i]
            return average / len(face_ids)

        elif self.type == MFn.kMeshVertComponent:
            return self._normals[idx]

    # def get_normals(self, space=api.MSpace.kWorld, angle_weighted=False):
    #     """
    #     """
    #     if self._normals is None:
    #         self.__mesh_normals(space, angle_weighted)
    #     normals = []
    #     for idx in self.indices:

    #     return [self._normals[idx] for idx in self.indices]

    def get_uv_shell(self):
        """
        Extend current :class:`Component` to contained uv shell and return new
        :class:``Component`` object.

        :rtype: :class:`Component`
        """
        uvs = self.to_map()
        count, array = self.mesh.getUvShellsIds()
        wanted = set([array[idx] for idx in self.indices])
        uvs.add([idx for idx, num in enumerate(array) if num in wanted])
        return uvs

    def is_complete(self):
        return self._indexed.isComplete

    def is_border(self, index):
        """
        Check if component index is on border of mesh.
        """
        if self.type == api.MFn.kMeshPolygonComponent:
            return self.mesh.onBoundary(self.to_face().index)
        elif self.type == api.MFn.kEdgeComponent:
            return cmds.polySelect(q=True, edgeBorder=index) or False
        else:
            edge = self.new().add(index).to_edge()
            return any(
                [cmds.polySelect(q=True, edgeBorder=i) for i in edge.indices]
                )
        return False

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

    def is_valid(self, comptype=None):
        """
        Whether this is a valid Component object or not.

        :param comptype: Internal ``OpenMaya.MFn`` int type.
        :rtype: ``bool``
        """
        if comptype is None:
            return not(self.object.isNull())
        return self.type == comptype

    def toggle(self, other=None):
        """
        Toggles Component objects with other objects.

        If other is not provided toggles with complete component object.

        :param other: :class:`Component`
        """
        if other is None:
            component = self.get_complete()
        else:
            if self.dagpath == other.dagpath:
                component = other
            else:
                logger.warn('{0} is not equal to {1}'.format(self, other))

        new = self.__class__(*self.node)
        new._slist.toggle(self.dagpath, component.object)
        return new

    def translate(self, **kwargs):
        """
        Translate components with given optional keyword arguments.

        :param \*\*kwargs: Optional keyword arguments ``cmds.xform`` takes.

        .. todo:: if self._bbox get new matrix and translate bbox with it.
        """
        cmds.xform(list(self), **kwargs)


class MeshVert(Component):
    __mtype__ = MFn.kMeshVertComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshVert, cls).create(dagpath, cls.__mtype__)


class MeshEdge(Component):
    __mtype__ = MFn.kMeshEdgeComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshEdge, cls).create(dagpath, cls.__mtype__)


class MeshPolygon(Component):
    __mtype__ = MFn.kMeshPolygonComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshPolygon, cls).create(dagpath, cls.__mtype__)


class MeshMap(Component):
    __mtype__ = MFn.kMeshMapComponent

    @classmethod
    def create(cls, dagpath):
        return super(MeshMap, cls).create(dagpath, cls.__mtype__)

    def translate(cls, **kwargs):
        cmds.polyEditUV(list(cls), **kwargs)


if __name__ == '__main__':

    # s = Component('pSphere1.f[237]')
    # s = Component('pSphere1.e[237]')
    s = Component('pPlane1.vtx[3]')
    # s = Component('pPlane1.e[9]')
    print s.is_border(s.index)
