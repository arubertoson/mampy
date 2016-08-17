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


def get_dagpath_from_string(input_string):
    return api.MSelectionList().add(input_string).getDagPath(0)


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
        self._attributes = set()

    # def __getattr__(self, key):
    #     if key in self._attributes:
    #         return self.get_plug(key).get()

    # def __setattr__(self, key, value):
    #     if key == '_attributes':
    #         return super(AbstractNode, self).__setattr__(key, value)

    #     if key in self._attributes:
    #         self.get_plug(key).set(value)
    #     else:
    #         super(AbstractNode, self).__setattr__(key, value)

    # __getitem__ = __getattr__
    # __setitem__ = __setattr__

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

    @property
    def attributes(self):
        if self._attributes is None:
            shortnames = cmds.listAttr(self.fullpath, shortName=True)
            longnames = cmds.listAttr(self.fullpath)
            self._attributes = set(shortnames + longnames)
        return self._attributes


# class DependencyNode(AbstractNode):

#     def __init__(self, dagpath):
#         super(DependencyNode, self).__init__()

#         self.dagpath = dagpath
#         self._mfndep = api.MSelectionList().add(dagpath).getDependNode(0)

#         self._plugs = None

#     @property
#     def fullpath(self):
#         return self._mfndep.name()

#     @property
#     def node(self):
#         return self._mfndep

#     @property
#     def mobject(self):
#         return self._mfndep.node()

#     def connect(self, attribute, other):
#         if isinstance(other, Plug):
#             self.get_plug(attribute).connect(other)
#         else:
#             self.get_plug(attribute).connect(self.get_plug(attribute))

#     def disconnect(self, attribute, other):
#         if isinstance(other, Plug):
#             self.get_plug(attribute).disconnect(other)
#         else:
#             self.get_plug(attribute).disconnect(self.get_plug(attribute))

#     @property
#     def plugs(self):
#         if self._plugs is None:
#             self._plugs = (Plug(p) for p in self._mfndep.getConnections())
#         return self._plugs

#     def exists(self):
#         return cmds.objectExists(self.fullpath)

class CleanSetAttrMeta(type):
    def __call__(cls, *args, **kwargs):
        real_setattr = cls.__setattr__
        cls.__setattr__ = object.__setattr__
        self = super(CleanSetAttrMeta, cls).__call__(*args, **kwargs)
        cls.__setattr__ = real_setattr
        return self


class Node(object):
    __metaclass__ = CleanSetAttrMeta

    def __new__(cls, dagpath, object=None):
        if isinstance(dagpath, basestring):
            dagpath = get_dagpath_from_string(dagpath)

        try:
            shape = api.MDagPath.getAPathTo(dagpath.child(0))
        except (RuntimeError, AttributeError):
            shape = dagpath

        for c in cls.__subclasses__():
            if c.__name__.lower() == cmds.nodeType(str(shape)):
                return super(Node, cls).__new__(c, dagpath, object)
        return super(Node, cls).__new__(cls, dagpath, object)

    def __init__(self, dagpath, object=None):
        # In case we create the node from subclass
        if isinstance(dagpath, basestring):
            dagpath = get_dagpath_from_string(dagpath)

        self._attributes = set()
        self._dagpath = dagpath
        self._mfnnode = object(dagpath)

    def __getattr__(self, key):
        if key in self.attributes:
            return self.get_plug(key).get()

    def __setattr__(self, name, value):
        if name == '_attributes':
            return super(Node, self).__setattr__(name, value)

        if name in self.attributes:
            self.get_plug(name).set(value)
        else:
            super(Node, self).__setattr__(name, value)

    __getitem__ = __getattr__
    __setitem__ = __setattr__

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{}'.format(self._mfnnode.fullPathName())

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
    def attributes(self):
        if not self._attributes:
            shortnames = cmds.listAttr(str(self), shortNames=True)
            longnames = cmds.listAttr(str(self))
            self._attributes = set(shortnames + longnames)
        return self._attributes

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
            return self.__class__(self._dagpath.extendToShape(0))
        except RuntimeError:
            return None

    @property
    def type(self):
        return self._dagpath.apiType()

    @property
    def typestr(self):
        return cmds.nodeType(str(self))

    @classmethod
    def from_mobject(cls, object):
        return cls(api.MDagPath.getAPathTo(object))

    def get_child(self, index=0):
        """
        Return child at given index. If index is not given return first
        in list.
        """
        try:
            return self.from_object(self._mfnnode.child(index))
        except RuntimeError:
            return None

    def get_parent(self, index=0):
        """
        Return parent at given index. If index is not given return
        first in list.
        """
        try:
            return self.from_object(self._mfnnode.parent(index))
        except RuntimeError:
            return None

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

    def get_transform(self):
        """
        Return the closest transform node from the given dagpath.
        """
        return Transform(self._dagpath.getAPathTo(self._dagpath.transform()))

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
            yield self.from_object(self._mfnnode.child(idx))

    def iterparents(self):
        """
        Iterates over the :class:`DagNode` ``api.OpenMaya.MObject`` parents.
        """
        for idx in xrange(self._mfnnode.parentCount()):
            yield self.from_object(self._mfnnode.parent(idx))

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
        return self.__class__(n)


class Camera(Node):

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


if __name__ == '__main__':
    persp = Node('persp1')
    persp_trsn = persp.get_transform()
    for i in persp_trsn.attributes:
        if i.startswith('r'):
            print i

    Cam = collections.namedtuple('Cam', 'translate rotate centerOfInterest')
    test = Cam(
        persp_trsn['translate'],
        persp_trsn['rotate'],
        persp['centerOfInterest'],
    )

    print test
    # if persp.is_ortho():
    #     persp['orthographic'] = False
    # else:
    #     vec = persp.get_view_direction()
    #     center = persp.get_center_of_interest().z
    #     vec_pos = vec * center

    #     # Get axis
    #     axes = [
    #         ('x', (1, 0, 0)),
    #         ('y', (0, 1, 0)),
    #         ('z', (0, 0, 1)),
    #         ('x', (-1, 0, 0)),
    #         ('y', (0, -1, 0)),
    #         ('z', (0, 0, -1)),
    #     ]
    #     best_vec = {}
    #     for axis, wv in axes:
    #         dot = vec * api.MVector(wv)
    #         if axis not in best_vec or (axis in best_vec and dot > best_vec[axis]):
    #             best_vec[axis] = dot
    #     axis = max(best_vec, key=best_vec.get)

    #     trans = persp.get_transform()
    #     transl = trans.get_translation()
    #     vec = transl - vec_pos
    #     for i in 'xyz'.replace(axis, ''):
    #         setattr(transl, i, getattr(vec, i))

    #     trans['translate'] = list(transl)

    #     persp_trans = persp.get_transform()
    #     rot = persp_trans.get_rotate()

    #     persp['orthographic'] = True
    #     persp['orthographicWidth'] = abs(center)
    #     persp_trans['rotateX'] = int(90 * round(float(rot.x)/90))
    #     persp_trans['rotateY'] = int(90 * round(float(rot.y)/90))
