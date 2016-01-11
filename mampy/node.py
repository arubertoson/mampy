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
import maya.OpenMaya as oldapi
import maya.api.OpenMaya as api

logger = logging.getLogger(__name__)


__all__ = ['DagNode', 'Camera', 'Transform']


def _space(kspace):
    return {
        api.MSpace.kWorld: {'worldSpace': True},
        api.MSpace.kObject: {'worldSpace': True},
    }[kspace]


class Plug(api.MPlug):
    """
    Wrapping API ``api.OpenMaya.MPlug`` for easier functionality.
    """

    def __init__(self, node, *args, **kwargs):
        self.node = node
        super(Plug, self).__init__(*args, **kwargs)

    @property
    def name(self):
        return '{}.{}'.format(self.node.fullpath, self.plug_name)

    @property
    def plug_name(self):
        return self.partialName(useLongNames=True)

    def get(self, *args, **kwargs):
        return cmds.getAttr(self.name, *args, **kwargs)

    def set(self, value, *args, **kwargs):
        cmds.setAttr(self.name, value, *args, **kwargs)

    def connect(self, other, *args, **kwargs):
        cmds.connectAttr(self.name, other.name, *args, **kwargs)

    def disconnect(self, other, *args, **kwargs):
        cmds.disconnectAttr(self.name, other.name, *args, **kwargs)


class DagFactory(type):
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


class DagNode(object):
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
    __metaclass__ = DagFactory

    def __init__(self, dagpath):
        self._dagpath = dagpath
        self._dagnode = api.MFnDagNode(dagpath)
        self._mfndep = api.MFnDependencyNode(dagpath.node())
        self._attr = None

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

    def __getattr__(self, name):
        if name in self.attributes:
            p = Plug(self, self._mfndep.findPlug(name, False))
            setattr(self, name, p)
            return p

    @property
    def attributes(self):
        """
        Construct and return attribute list that belongs to node.

        :rtype: ``list``
        """
        if self._attr is None:
            attributes = set(cmds.listAttr(self.fullpath, shortNames=True))
            attributes.update(set(cmds.listAttr(self.fullpath)))
            self._attr = attributes
        return self._attr

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
        return self._dagpath.node()

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
        return self._dagnode.hasParent(other.node)

    def is_parent_of(self, other):
        return self._dagnode.hasChild(other.node)

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

        s = oldapi.MSelectionList(); s.add(self.fullpath)
        dp = oldapi.MDagPath(); s.getDagPath(0, dp)
        self._mfncam = oldapi.MFnCamera(dp)

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
    p = set([DagNode('pCube5'), DagNode('pCube3')])
    c = set([DagNode('pCube5'), DagNode('pCube3')])


    print p == c
    # trns = p.get_transform()
    # trns.set_pivot(api.MVector(0, 0, 0))


    # cm = c._dagnode.transformationMatrix()
    # pm = p._dagnode.transformationMatrix()

    # m = cm - pm
    # print type(m)
    # c._dagnode.addChild(p.node)
    # # p.translate.set(0, 0, 0)

    # trans = p.get_transform()
    # m = api.MTransformationMatrix(m)
    # t = m.translation(api.MSpace.kWorld)
    # trans._mfntrans.setTranslation(t, api.MSpace.kWorld)
