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
import collections

from maya import cmds
import maya.api.OpenMaya as api
from maya.api.OpenMaya import MFn


def get_dagpath_from_string(input_string):
    return api.MSelectionList().add(input_string).getDagPath(0)


def get_dependency_from_string(input_string):
    return api.MSelectionList().add(input_string).getDependNode(0)


class NodeAttributes(collections.MutableMapping):

    def __init__(self, iterable=None):
        self.elements = {}

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.elements.keys())

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, name):
        return self.elements[name].get()

    def __setitem__(self, name, value):
        if name in self.elements:
            self.elements[name].set(value)
        else:
            self.elements[name] = value

    def __delitem__(self, name):
        del self.elements[name]

    def plug(self, name):
        return self.elements[name]

    def connect(self, name, other):
        return self.elements[name].connect(other)

    def disconnect(self, name, other):
        return self.elements[name].disconnect(other)


class Plug(object):
    """
    Wrapping API ``api.OpenMaya.MPlug`` for easier functionality.
    """

    def __init__(self, node, plug):
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
        return '{}.{}'.format(str(self.depnode), self.plug_name)

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


class AbstractNode(object):

    def __init__(self):
        self._attr = NodeAttributes()

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{}'.format(self._mfnnode.fullPathName())

    @property
    def attr(self):
        attr_list = self.attributes() - set(self._attr.keys())
        if attr_list:
            for name in attr_list:
                try:
                    self._attr[name] = self.get_plug(name)
                except AttributeError:
                    continue
        return self._attr

    def get_plug(self, name):
        """
        Construct and return Plug object.

        :rtype: :class:`Plug`
        """
        try:
            return Plug(self, self._mfnnode.findPlug(name, False))
        except RuntimeError:
            raise AttributeError('{} object has no attribute "{}"'.format(
                                 self.__class__.__name__, name))

    def attributes(self):
        return set(cmds.listAttr(str(self), shortNames=True) + cmds.listAttr(str(self)))


class DependencyNode(AbstractNode):

    def __init__(self, dagpath):
        super(DependencyNode, self).__init__()
        if isinstance(dagpath, basestring):
            dagobject = get_dependency_from_string(dagpath)
        else:
            dagobject = dagpath

        self.dagpath = dagpath
        self._mfnnode = api.MFnDependencyNode(dagobject)

        self._plugs = None

    def __str__(self):
        return '{}'.format(self._mfnnode.name())

    def __contains__(self, name):
        return self._mfnnode.hasAttribute(name)

    @property
    def node(self):
        return self._mfnnode

    @property
    def mobject(self):
        return self._mfnnode.node()

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
            self._plugs = (Plug(p) for p in self._mfnnode.getConnections())
        return self._plugs

    def exists(self):
        return cmds.objExists(str(self))


class Node(AbstractNode):

    def __new__(cls, dagpath, object=None):
        if isinstance(dagpath, basestring):
            dagpath = get_dagpath_from_string(dagpath)

        for c in cls.__subclasses__():
            if c._mtype == dagpath.apiType():
                return super(Node, cls).__new__(c, dagpath, object)
        return super(Node, cls).__new__(cls, dagpath, object)

    def __init__(self, dagpath, object=None):
        super(Node, self).__init__()
        # In case we create the node from subclass
        if isinstance(dagpath, basestring):
            dagpath = get_dagpath_from_string(dagpath)

        self._dagpath = dagpath
        self._mfnnode = api.MFnDagNode(dagpath) if object is None else object(dagpath)
        self._mfntransform = None

    def __eq__(self, other):
        return self._dagpath == other._dagpath

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self._dagpath.isValid()

    def __hash__(self):
        return hash(str(self))

    def __contains__(self, mobject):
        """
        .. note:: Just here for backwards compability.
        """
        return self._mfnnode.hasChild(mobject)

    @property
    def dagpath(self):
        return self._dagpath

    @property
    def short_name(self):
        return self.node.partialPathName()

    @property
    def bbox(self):
        return self._mfnnode.boundingBox

    @property
    def node(self):
        return self._mfnnode

    @property
    def matrix(self):
        return self._mfnnode.transformationMatrix()

    @property
    def mobject(self):
        return self._dagpath.node()

    @property
    def shape(self):
        try:
            return Node(self._dagpath.extendToShape(0))
        except RuntimeError:
            return None

    @property
    def transform(self):
        """
        Return the closest transform node from the given dagpath.
        """
        if isinstance(self.__class__, Transform):
            return self
        else:
            if self._mfntransform is None:
                self._mfntransform = Transform(self._dagpath.getAPathTo(
                                               self._dagpath.transform()))
            return self._mfntransform

    @property
    def type(self):
        return self._dagpath.apiType()

    @property
    def typestr(self):
        return self.mobject.apiTypeStr

    @classmethod
    def from_mobject(cls, object):
        return Node(api.MDagPath.getAPathTo(object))

    def get_child(self, index=0):
        """
        Return child at given index. If index is not given return first
        in list.
        """
        try:
            return self.from_mobject(self._mfnnode.child(index))
        except RuntimeError:
            return None

    def get_parent(self, index=0):
        """
        Return parent at given index. If index is not given return
        first in list.
        """
        try:
            return self.from_mobject(self._mfnnode.parent(index))
        except RuntimeError:
            return None

    def is_child_of(self, other):
        return self._mfnnode.hasParent(other.mobject)

    def is_parent_of(self, other):
        return self._mfnnode.hasChild(other.mobject)

    def is_root(self):
        p = self.get_parent()
        return p is None or p.type == api.MFn.kWorld

    def iterchildren(self):
        """
        Iterates over the :class:`DagNode` ``api.OpenMaya.MObject`` children.
        """
        for idx in xrange(self._mfnnode.childCount()):
            yield self.from_mobject(self._mfnnode.child(idx))

    def iterparents(self):
        """
        Iterates over the :class:`DagNode` ``api.OpenMaya.MObject`` parents.
        """
        for idx in xrange(self._mfnnode.parentCount()):
            yield self.from_mobject(self._mfnnode.parent(idx))

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
            n = cmds.parent(str(self), other, **kwargs)[0]
        elif other is None or other.type == api.MFn.kWorld:
            n = cmds.parent(str(self), world=True, **kwargs)[0]
        else:
            n = cmds.parent(str(self), str(other), **kwargs)[0]
        return self.__class__(n)


class Camera(Node):

    _mtype = MFn.kCamera

    def __init__(self, dagpath):
        super(Camera, self).__init__(dagpath, api.MFnCamera)

    def get_view_direction(self, space=api.MSpace.kWorld):
        return self._mfnnode.viewDirection(space)

    def get_center_of_interest(self, space=api.MSpace.kWorld):
        return self._mfnnode.centerOfInterestPoint()

    def is_ortho(self):
        return self._mfnnode.isOrtho()


def _space(kspace):
    return {
        api.MSpace.kWorld: {'worldSpace': True},
        api.MSpace.kObject: {'worldSpace': True},
    }[kspace]


class Transform(Node):
    _mtype = MFn.kTransform
    Transforms = collections.namedtuple('Transforms', 'translate rotate scale')

    def __init__(self, dagpath):
        super(Transform, self).__init__(dagpath, api.MFnTransform)

    def get_transforms(self):
        return self.Transforms(
            self.get_translation(),
            self.get_rotate(),
            self.get_scale(),
        )

    def get_rotate_pivot(self, space=api.MSpace.kWorld):
        return api.MVector(self._mfnnode.rotatePivot(space))

    def get_scale_pivot(self, space=api.MSpace.kWorld):
        return api.MVector(self._mfnnode.scalePivot(space))

    def get_translation(self, space=api.MSpace.kWorld):
        return self._mfnnode.translation(space)

    def get_rotate(self):
        return api.MVector([math.degrees(i)
                           for i in self._mfnnode.rotation()])

    def get_scale(self):
        return api.MVector(self._mfnnode.scale())

    def set_pivot(self, point, space=api.MSpace.kWorld):
        if isinstance(point, api.MVector):
            point = api.MPoint(point)
        cmds.xform(self._dagpath, pivots=list(point)[:3], **_space(space))
