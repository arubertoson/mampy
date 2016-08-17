"""
"""
from maya import cmds

import maya.OpenMaya as oapi
from maya.OpenMaya import MGlobal


def get_active_flags_in_mask(object=True):
    """
    Return dict object with current state of flags in selection mask.
    """
    object_flags = [
        'handle', 'ikHandle', 'ikEndEffector', 'joint', 'light',
        'camera', 'lattice', 'cluster', 'sculpt', 'nonlinear', 'nurbsCurve',
        'nurbsSurface', 'curveOnSurface', 'polymesh', 'subdiv', 'stroke',
        'plane', 'particleShape', 'emitter', 'field', 'fluid', 'hairSystem',
        'follicle', 'nCloth', 'nRigid', 'dynamicConstraint', 'nParticleShape',
        'collisionModel', 'spring', 'rigidBody', 'rigidConstraint',
        'locatorXYZ', 'orientationLocator', 'locatorUV', 'dimension',
        'texture', 'implicitGeometry', 'locator', 'curve'
    ]
    component_flags = [
        'controlVertex', 'hull', 'editPoint', 'polymeshVertex',
        'polymeshEdge', 'polymeshFreeEdge', 'polymeshFace', 'polymeshUV',
        'polymeshVtxFace', 'vertex', 'edge', 'facet', 'curveParameterPoint',
        'curveKnot', 'surfaceParameterPoint', 'surfaceKnot', 'surfaceRange',
        'surfaceEdge', 'surfaceFace', 'surfaceUV', 'isoparm',
        'subdivMeshPoint', 'subdivMeshEdge', 'subdivMeshFace', 'subdivMeshUV',
        'latticePoint', 'particle', 'springComponent', 'jointPivot',
        'scalePivot', 'rotatePivot', 'selectHandle', 'localRotationAxis',
        'imagePlane',
    ]
    flag_list = object_flags if object else component_flags
    return [i for i in flag_list if cmds.selectType(q=True, **{i: True})]


def get_active_select_mode():
    """
    Return the current selection mode.
    """
    for i in [
        'component', 'hierarchical', 'leaf', 'object', 'preset', 'root', 'template'
    ]:
        if cmds.selectMode(q=True, **{i: True}):
            return i


class SelectionMask(object):
    """
    Selection mask class for accessing and changing selection mask
    information.
    """

    (kSelectObjectMode,
     kSelectComponentMode,
     kSelectRootModem,
     kSelectLeafMode,
     kSelectTemplateMode) = range(5)

    def __new__(cls, mask=None):
        cls = object.__new__(cls, mask)
        for a in oapi.MSelectionMask.__dict__:
            if a.startswith('kSelect'):
                setattr(cls, a, oapi.MSelectionMask.__dict__[a])
        return cls

    def __init__(self, mask=None):
        self._mask = mask or oapi.MSelectionMask()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, list(self))

    def __str__(self):
        return '{}'.format(self.typestr)

    def __iter__(self):
        return iter(self.get_active_masks(local=True))

    def __contains__(self, value):
        return self._mask.intersects(value)

    @property
    def mask(self):
        return self._mask

    @property
    def mode(self):
        return MGlobal.selectionMode()

    @property
    def typestr(self):
        return self.get_active_masks(internal=False, local=True)

    @classmethod
    def active(cls):
        """
        Return active selection mask.
        """
        mask = {
            MGlobal.kSelectObjectMode: MGlobal.objectSelectionMask(),
            MGlobal.kSelectComponentMode: MGlobal.componentSelectionMask(),
        }[MGlobal.selectionMode()]
        return cls(mask)

    @staticmethod
    def set_mode(kmode):
        """
        Set selection mode.

        :param kmode: internal selection mode pointer.
        """
        MGlobal.setSelectionMode(kmode)

    def add(self, other):
        """
        Add mask(s) to the current :class:`SelectionMask` object.
        """
        if type(other) in [list, tuple, set]:
            for o in other:
                self._mask.addMask(o)
        else:
            self._mask.addMask(other)
        self.update()

    def set_mask(self, other):
        """
        Set active mask to given ``OpenMaya.MSelectionMask`` or
        internal int pointer.
        """
        self._mask.setMask(other)
        self.update()

    def get_active_masks(self, internal=True, local=False):
        """
        Construct and return active mask set.

        :param internal: wether rtype is internal int pointers or
            string attributes.
        :param local: wether to look for masks in local ``SelectionMask``
            object or global ``OpenMaya.MGlobal`` mask.
        :rtype: ``set``
        """
        active = set()
        for m in self.__dict__:
            if not m.startswith('kSelect'):
                continue

            if local:
                space = self
            else:
                space = self.active()

            if self.__dict__[m] in space:
                if internal:
                    active.add(self.__dict__[m])
                else:
                    active.add(m)
        return active

    def clear(self):
        """
        Empty mask by creating new one and overriding it.
        """
        self._mask = oapi.MSelectionMask()
        self.update()

    def update(self):
        """
        Set to be the active mask in Maya.
        """
        if self.mode == MGlobal.kSelectComponentMode:
            MGlobal.setComponentSelectionMask(self._mask)
        elif self.mode == MGlobal.kSelectObjectMode:
            MGlobal.setObjectSelectionMask(self._mask)
