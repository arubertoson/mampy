# -*- coding: utf-8 -*-

"""
    mampy.component
    ~~~~~~~~~~~~~~~

    Classes for Maya component types.

"""
import logging
import itertools

# Maya API import
import maya.cmds as cmds
try:
    import maya.api.OpenMaya as api
    from maya.api.OpenMaya import MFn
except ImportError:
    import maya.OpenMaya as api
    from maya.OpenMaya import MFn


logger = logging.getLogger(__name__)


class ComponentFactory(type):

    def __call__(cls, dagpath, compobj=None):
        """Constructs A Component from a dagpath string or dagpath and
        component object.

        Depending on the object type return the right type class.
        """
        if isinstance(dagpath, basestring):
            slist = api.MSelectionList()
            slist.add(dagpath)
            dagpath, compobj = slist.getComponent(0)

        try:
            cls = {
                MFn.kMeshVertComponent: MeshVert,
                MFn.kMeshEdgeComponent: MeshEdge,
                MFn.kMeshPolygonComponent: MeshPolygon,
                MFn.kMeshMapComponent: MeshMap,
            }[compobj.apiType()]
        except KeyError:
            logger.warn('Component object is Null.')

        self = object.__new__(cls)
        self._init(dagpath, compobj)
        return self


class Component(object):
    """class Component(dagpath, mobject)

    Provides general functionality for working with Component objects.

    TODO:
        - Docstring

    """
    __metaclass__ = ComponentFactory
    TYPESTR = {
        MFn.kMeshVertComponent: 'vtx',
        MFn.kMeshPolygonComponent: 'f',
        MFn.kMeshEdgeComponent: 'e',
        MFn.kMeshVtxFaceComponent: 'vtxFace',
        MFn.kMeshMapComponent: 'map',
    }
    SET_COMPLETE = {
        MFn.kMeshPolygonComponent: 'numPolygons',
        MFn.kMeshEdgeComponent: 'numEdges',
        MFn.kMeshVertComponent: 'numVertices',
        MFn.kMeshMapComponent: 'numUVs'
    }

    def _init(self, dagpath, compobj):
        self.dagpath = dagpath
        self.object = compobj
        self.space = api.MSpace.kWorld

        self._slist = api.MSelectionList()
        self._slist.add((self.dagpath, self.object))

        self._indexed = api.MFnSingleIndexedComponent(self.object)
        self._bbox = None
        self._mesh = None
        self._points = None

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
            r = self._slist.getSelectionStrings()
        return '{}'.format(r)

    def __len__(self):
        return self._indexed.elementCount

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

    @classmethod
    def create(cls, dagpath, comptype):
        if isinstance(dagpath, basestring):
            tmp = api.MSelectionList()
            tmp.add(dagpath)
            dagpath = tmp.getDagPath(0)

        indexed = api.MFnSingleIndexedComponent()
        cobj = indexed.create(comptype)
        cfn = api.MFnComponent(cobj)
        cfn.setObject(dagpath.node())
        return cls(dagpath, cobj)

    @property
    def bounding_box(self):
        if self._bbox is None:
            pmax = api.MPoint(map(max, itertools.izip(*self.points)))
            pmin = api.MPoint(map(min, itertools.izip(*self.points)))
            self._bbox = api.MBoundingBox(pmax, pmin)
        return self._bbox

    @property
    def indices(self):
        return self._indexed.getElements()

    @property
    def node(self):
        """The node property represents the component as a tuple with the
        dagpath and component object."""
        return (self.dagpath, self.object)

    @property
    def mesh(self):
        if self._mesh is None:
            self._mesh = api.MFnMesh(self.dagpath)
        return self._mesh

    @property
    def points(self):
        """Collection of position data for the existing points in current
        object."""
        if self._points is None:
            if self.type == MFn.kMeshMapComponent:
                self._points = zip(*self.mesh.getUVs())
                if not self._indexed.isComplete:
                    self._points = [self._points[idx] for idx in self.indices]
            else:
                self._points = self.mesh.getPoints(self.space)
                if not self._indexed.isComplete:
                    self._points = [self._points[idx] for idx in self.indices]
        return self._points

    @property
    def type(self):
        return self.object.apiType()

    @property
    def typestr(self):
        return self.object.apiTypeStr

    def add(self, indices):
        if hasattr(indices, '__len__'):
            self._indexed.addElements(indices)
        else:
            self._indexed.addElement(indices)
        self._slist.add(self.node)

    def to_face(self, **kwargs):
        return self.convert_to(toFace=True, **kwargs)

    def to_edge(self, **kwargs):
        return self.convert_to(toEdge=True, **kwargs)

    def to_vert(self, **kwargs):
        return self.convert_to(toVertex=True, **kwargs)

    def to_map(self, **kwargs):
        return self.convert_to(toUV=True, **kwargs)

    def to_vtxFace(self, **kwargs):
        return self.convert_to(toVertexFace=True, **kwargs)

    def convert_to(self, **kwargs):
        """Converts components in selection list to given component type."""
        s = api.MSelectionList()
        for dp in cmds.polyListComponentConversion(list(self), **kwargs):
            s.add(dp)

        if s.isEmpty():
            logger.warn(
                'Failed to convert {} with keywords: {}'
                .format(list(self), kwargs)
            )

        return self.__class__(*s.getComponent(0))

    def get_complete(self):
        attr = getattr(self.mesh, self.SET_COMPLETE[self.type])
        count = attr() if hasattr(attr, '__call__') else attr

        # Create new complete component object.
        complete = self.create(self.dagpath, self.type)
        complete._indexed.setCompleteData(count)
        return self.__class__(self.dagpath, complete.object)

    def get_mesh_shell(self):
        """Return new Component class extended to mesh shells."""
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

    def get_uv_shell(self):
        """Return new Component class extended to uv shells."""
        uvs = self.to_map()
        count, array = self.mesh.getUvShellsIds()
        wanted = set([array[idx] for idx in self.indices])
        uvs.add([idx for idx, num in enumerate(array) if num in wanted])
        return uvs

    def is_empty(self):
        return self._slist.isEmpty()

    def is_face(self):
        return self.is_valid(MFn.kMeshPolygonComponent)

    def is_edge(self):
        return self.is_valid(MFn.kMeshEdgeComponent)

    def is_vert(self):
        return self.is_valid(MFn.kMeshVertComponent)

    def is_map(self):
        return self.is_valid(MFn.kMeshMapComponent)

    def is_vtxFace(self):
        return self.is_valid(MFn.kMeshVtxFaceComponent)

    def is_valid(self, comptype=None):
        """Whether this is a valid component user can do work with."""
        if self.object.isNull():
            return False

        if comptype is not None and self.type == comptype:
            return True
        else:
            return not(self.is_empty())

    def toggle(self, other=None):
        """Toggles components.

        If other is not given assume user wants to toggle complete component.
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
        # TODO: If bbox, get new matrix and translate it. Much cheaper than
        #       calculating again.
        cmds.xform(list(self), **kwargs)


class MeshEdge(Component):
    """Mesh edge class."""


class MeshPolygon(Component):
    """Mesh polygon class."""


class MeshVert(Component):
    """Mesh vertex class."""


class MeshMap(Component):
    """Mesh map class."""

    def translate(self, **kwargs):
        cmds.polyEditUV(list(self), **kwargs)
