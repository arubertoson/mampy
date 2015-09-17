# -*- coding: utf-8 -*-

"""
    mampy.nodes
    ~~~~~~~~~~~

    Classes for Maya node types.

    .. todo:: module docstring.

"""
import logging

import maya.cmds as cmds
import maya.OpenMaya as oldapi
import maya.api.OpenMaya as api

logger = logging.getLogger(__name__)


__all__ = ['DagNode', 'Camera']


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
        except RuntimeError:
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

    def __contains__(self, mobject):
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

    def get_shape(self, index=0):
        """
        Return shape at given index. If index is not given return first
        in list.
        """
        return self.__class__(self._dagpath.extendToShape(index))

    def get_parent(self, index=0):
        """
        Return parent at given index. If index is not given return
        first in list.
        """
        return self.from_object(self._dagnode.parent(index))

    def get_child(self, index=0):
        """
        Return child at given index. If index is not given return first
        in list.
        """
        return self.from_object(self._dagnode.child(index))

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


if __name__ == '__main__':
    t = cmds.ls(sl=True).pop()
    c = DagNode(t)
    print c
