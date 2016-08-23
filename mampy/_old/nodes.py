# -*- coding: utf-8 -*-

"""
    mampy.nodes
    ~~~~~~~~~~~

    Classes for Maya node types.

    .. todo::
        * module docstring.
        * rewrite as plugin? As it stands the script collection can't
        be used with certain api functions.
        * look into options for undo/redo functionality with api

"""
import math
import logging
import collections

import maya.cmds as cmds
import maya.OpenMaya as _oldapi
import maya.api.OpenMaya as api

logger = logging.getLogger(__name__)


__all__ = ['DagNode', 'DependencyNode', 'Camera', 'Transform']


def _space(kspace):
    return {
        api.MSpace.kWorld: {'worldSpace': True},
        api.MSpace.kObject: {'worldSpace': True},
    }[kspace]


class Plug(object):
    """
    Wrapping API ``api.OpenMaya.MPlug`` for easier functionality.
    """

    def __init__(self, node, plug):
        print 'getplug', repr(node), repr(plug)
        self.depnode = node
        self._mfnplug = plug

    def __str__(self):
        return str(cmds.getAttr(self.name))

    @property
    def node(self):
        return self._mfnplug

    @property
    def mobject(self):
        return self._mfnplug.node()

    @property
    def name(self):
        return '{}.{}'.format(self.depnode.fullpath, self.plug_name)

    @property
    def plug_name(self):
        return self._mfnplug.partialName(useLongNames=True)

    def get(self, *args, **kwargs):
        result = cmds.getAttr(self.name, *args, **kwargs)
        if isinstance(result, (tuple, list)):
            return result[0]
        else:
            return result

    def set(self, value, *args, **kwargs):
        if hasattr(value, '__iter__') and not isinstance(value, basestring):
            cmds.setAttr(self.name, *list(value), **kwargs)
        else:
            cmds.setAttr(self.name, value, *args, **kwargs)

    def connect(self, other, *args, **kwargs):
        cmds.connectAttr(self.name, other.name, *args, **kwargs)

    def disconnect(self, other, *args, **kwargs):
        cmds.disconnectAttr(self.name, other.name, *args, **kwargs)


class NodeBase(object):

    def __init__(self):
        self._attributes = None
        self._mfndep = None
        self._fullpath = None
        # self.__initialised = True

    def __getattr__(self, name):
        if name in self.attributes:
            plug = self.get_plug(name)
            return plug.get()

    def __setattr__(self, name, value):
        # Needed to be able to set attributes in __init__
        if '_{}__initialised'.format(self.__class__.__name__) not in self.__dict__:
            return dict.__setattr__(self, name, value)
        # to stop recursive when calling property
        elif name == '_attributes':
            return super(NodeBase, self).__setattr__(name, value)

        if name in self.attributes:
            self.get_plug(name).set(value)
        else:
            super(NodeBase, self).__setattr__(name, value)

    __getitem__ = __getattr__
    __setitem__ = __setattr__

    def get_plug(self, name):
        """
        Construct and return Plug object.

        :rtype: :class:`Plug`
        """
        try:
            return Plug(self, self._mfndep.findPlug(name, False))
        except RuntimeError:
            raise AttributeError('{} object has no attribute "{}"'.format(
                                 self.__class__.__name__, name))

    @property
    def attributes(self):
        """
        Construct and return attribute list that belongs to node.

        :rtype: ``set``
        """
        if self._attributes is None:
            attributes = set(cmds.listAttr(self.fullpath, shortNames=True))
            attributes.update(set(cmds.listAttr(self.fullpath)))
            self._attributes = attributes
        return self._attributes


class DependencyNode(NodeBase):
    """
    A base dependency node class.

    Dependency nodes in maya contains a node and all its conenctions and
    attributes.

    .. todo:: Expand
    """

    def __init__(self, dagpath):
        super(DependencyNode, self).__init__()

        self.dagpath = dagpath
        tmp = api.MSelectionList(); tmp.add(dagpath)
        self._mfndep = api.MFnDependencyNode(tmp.getDependNode(0))

        self._plugs = None

        # Finished init
        self.__initialised = True

    @property
    def node(self):
        return self._mfndep

    @property
    def exists(self):
        return cmds.objExists(self.fullpath)

    @property
    def fullpath(self):
        return self._mfndep.name()

    def connect(self, attribute, other):
        if isinstance(other, Plug):
            self.get_plug(attribute).connect(other)
        else:
            self.get_plug(attribute).connect(self.get_plug(attribute))

    def disconnect(self, attribute, other):
        if isinstance(other, Plug):
            self.get_plug(attribute).disconnect(other)
        else:
            self.get_plug(attribute).disconnect(self.get_plug(attribute))

    @property
    def plugs(self):
        if self._plugs is None:
            self._plugs = (Plug(p) for p in self._mfndep.getConnections())
        return self._plugs


class DagNodeFactory(type):
    """Constructs a DagNode from a dagpath or dagpath object.

    Returns the DagNode subclass that represents the node type of given
    dagpath. If no subclass can be found returns DagNode object.
    """

    def __call__(cls, dagpath):
        if isinstance(dagpath, basestring):
            tmp = api.MSelectionList(); tmp.add(dagpath)
            dagpath = tmp.getDagPath(0)

        if cls is not DagNode:
            return type.__call__(cls, dagpath)

        try:
            shape = api.MDagPath.getAPathTo(dagpath.child(0))
        except (RuntimeError, AttributeError):
            shape = dagpath

        for c in cls.__subclasses__():
            if c.__name__.lower() == cmds.nodeType(str(shape)):
                cls = c
                break

        return type.__call__(cls, dagpath)


class DagNode(NodeBase):
    """
    A base dagnode class, providing most behaviour that Maya Nodes can
    inherit and override, as necessary.

    :param dagpath: dagpath str, ``api.OpenMaya.MDagPath``

    Usage::

        >>> import mampy
        >>> node = mampy.DagNode('pCube1')
        DagNode('|pCube1')

    .. note::

        :class:`DagNode` does currently lack subclasses. This will be
        developed as need arises.
    """
    __metaclass__ = DagNodeFactory

    def __init__(self, dagpath):
        super(DagNode, self).__init__()
        self._dagpath = dagpath
        self._dagnode = api.MFnDagNode(dagpath)
        self._mfndep = api.MFnDependencyNode(self.mobject)
        self._dependency = DependencyNode(dagpath)

        # Finished init
        self.__initialised = True

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{}'.format(self.fullpath)

    def __eq__(self, other):
        return self._dagpath == other._dagpath

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.node.isNull()

    def __hash__(self):
        return hash(self.fullpath)

    def __contains__(self, mobject):
        """
        .. note:: Just here for backwards compability.
        """
        return self.hasChild(mobject)

    @property
    def bounding_box(self):
        """
        :rtype: ``api.OpenMaya.MBoundingBox``
        """
        return self._dagnode.boundingBox

    @property
    def name(self):
        """
        :rtype: ``str``
        """
        return str(self._dagpath)

    @property
    def node(self):
        """
        :rtype: ``api.OpenMaya.MObject``
        """
        return self._dagpath

    @property
    def mobject(self):
        return self._dagpath.node()

    @property
    def dependency(self):
        return self._dependency

    @property
    def fullpath(self):
        """
        :rtype: ``str``
        """
        return self._dagpath.fullPathName()

    @property
    def matrix(self):
        """
        :rtype: ``api.OpenMaya.MMatrix``
        """
        return self._dagnode.transformationMatrix()

    @property
    def type(self):
        """
        :rtype: ``int``
        """
        return self._dagpath.apiType()

    @property
    def typestr(self):
        """
        :rtype: ``str``
        """
        return cmds.nodeType(self.fullpath)

    @classmethod
    def from_object(cls, mobject):
        return cls(api.MDagPath.getAPathTo(mobject))

    def set_parent(self, other, **kwargs):
        """
        .. todo::

            * try to avoid using cmds, find a way to update matrix after
            using addChild.

        .. note::
            Don't know if its possible with api commands since you would have
            to write an undo function of some kind.
        """
        if isinstance(other, basestring):
            n = cmds.parent(self.name, other, **kwargs)[0]
        elif other is None or other.type == api.MFn.kWorld:
            n = cmds.parent(self.name, world=True, **kwargs)[0]
        else:
            n = cmds.parent(self.name, other.name, **kwargs)[0]
        self = self.__class__(n)
        return self

    def get_child(self, index=0):
        """
        Return child at given index. If index is not given return first
        in list.
        """
        try:
            return self.from_object(self._dagnode.child(index))
        except RuntimeError:
            return None

    def get_parent(self, index=0):
        """
        Return parent at given index. If index is not given return
        first in list.
        """
        try:
            return self.from_object(self._dagnode.parent(index))
        except RuntimeError:
            return None

    def get_shape(self, index=0):
        """
        Return shape at given index. If index is not given return first
        in list.
        """
        try:
            shape = self.__class__(self._dagpath.extendToShape(index))
            self._dagpath = self._dagnode.dagPath()
            return shape
        except RuntimeError:
            return None

    def get_transform(self):
        """
        Return the closest transform node from the given dagpath.
        """
        return Transform(self._dagpath.getAPathTo(self._dagpath.transform()))

    def is_child_of(self, other):
        return self._dagnode.hasParent(other.mobject)

    def is_parent_of(self, other):
        return self._dagnode.hasChild(other.mobject)

    def is_root(self):
        p = self.get_parent()
        return p is None or p.type == api.MFn.kWorld

    def iterchildren(self):
        """
        Iterates over the :class:`DagNode` ``api.OpenMaya.MObject`` children.
        """
        for idx in xrange(self._dagnode.childCount()):
            yield self.from_object(self._dagnode.child(idx))

    def iterparents(self):
        """
        Iterates over the :class:`DagNode` ``api.OpenMaya.MObject`` parents.
        """
        for idx in xrange(self._dagnode.parentCount()):
            yield self.from_object(self._dagnode.parent(idx))


class Camera(DagNode):
    """
    Wraps ``OpenMaya.MFnCamera``.
    """

    def __init__(self, dagpath):
        super(Camera, self).__init__(dagpath)

        self._mfncam = api.MFnCamera(dagpath)

    def get_view_direction(self, space=api.MSpace.kWorld):
        """
        Return the view direction for the camera.

        :rtype: ``api.OpenMaya.MVector``
        """
        v = self._mfncam.viewDirection(space)
        return api.MVector(v.x, v.y, v.z)

    # def get_up_direction(self, space=api.MSpace.kWorld):
        # return api.MVector(self._mfncam.upDirection(space))


class Transform(DagNode):
    """
    Wraps ``OpenMaya.MFnTransform``.
    """

    Transforms = collections.namedtuple('Transforms', 'translate rotate scale')

    def __init__(self, dagpath):
        super(Transform, self).__init__(dagpath)
        self._mfntrans = api.MFnTransform(dagpath)

    def get_transforms(self):
        return self.Transforms(
            self.get_translation(),
            self.get_rotate(),
            self.get_scale(),
        )

    def get_rotate_pivot(self, space=api.MSpace.kWorld):
        return api.MVector(self._mfntrans.rotatePivot(space))

    def get_scale_pivot(self, space=api.MSpace.kWorld):
        return api.MVector(self._mfntrans.scalePivot(space))

    def get_translation(self, space=api.MSpace.kWorld):
        return self._mfntrans.translation(space)

    def get_rotate(self):
        return api.MVector([math.degrees(i)
                           for i in self._mfntrans.rotation()])

    def get_scale(self):
        return api.MVector(self._mfntrans.scale())

    def set_pivot(self, point, space=api.MSpace.kWorld):
        if isinstance(point, api.MVector):
            point = api.MPoint(point)
        cmds.xform(self._dagpath, pivots=list(point)[:3], **_space(space))

    # Needs a doIt function to register undo function
    #     self._mfntrans.setRotatePivot(point, space, True)
    #     self._mfntrans.setScalePivot(point, space, True)

    # def set_rotate_pivot(self, point, space=api.MSpace.kWorld):
    #     if isinstance(point, api.MVector):
    #         point = api.MPoint(point)
    #     self._mfntrans.setRotatePivot(point, space, True)

    # def set_scale_pivot(self, point, space=api.MSpace.kWorld):
    #     if isinstance(point, api.MVector):
    #         point = api.MPoint(point)
    #     self._mfntrans.setScalePivot(point, space, True)


if __name__ == '__main__':
    from maya.api import OpenMaya as api

    sl = api.MSelectionList()
    for i in cmds.ls('polyBevel*'):
        sl.add(i)

    for i in xrange(sl.length()):
        dep = api.MFnDependencyNode(sl.getDependNode(i))
        plug = dep.findPlug('fraction', False)
        # print plug.array()
        print dep.getConnections()

        # plug = sl.getPlug(i)
        # print plug.node().isNull()
        # print sl.getComponent(i)

