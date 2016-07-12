# -*- coding: utf-8 -*-
"""
Module to store containers.
"""
import logging
import textwrap
import collections

from maya import cmds, mel
import maya.OpenMaya as oldapi
from maya.OpenMaya import MGlobal as mgl
from maya.api import OpenMaya as api


from mampy.dgcomps import Component
from mampy.dgnodes import DagNode

logger = logging.getLogger(__name__)


class SelectionList(object):
    """
    A sequence like object wrapping the ``api.OpenMaya.MSelectionList``
    object.

    Emulates the ``api.OpenMaya.MSelectionList`` while trying to behave
    like a list object. The objects in the list can be fetched by index
    making the __iter__ a bit useless. I've taken advantage of this and
    made the __iter__ refer to ``MSelectionList.getSelectionStrings()``
    to fetch the readable string list that maya usually provides
    through ``cmds.ls`` function. This makes :class:`SelectionList`
    easier to pass around.

    Usage::

        >>> import mampy
        >>> slist = mampy.SelectionList()
        SelectionList([])
        ...
        >>> cmds.ls(sl=True)
        ['pCube1', 'pCube2']
        ...
        >>> slist.extend(cmds.ls(sl=True))
        SelectionList([u'pCube1', u'pCube2'])
    """

    def __init__(self, slist=None, merge=True):
        if isinstance(slist, api.MSelectionList):
            self._slist = api.MSelectionList(slist)

        elif type(slist) in [set, list, tuple]:
            self._slist = api.MSelectionList()
            for dagstr in slist:
                tmp = api.MSelectionList()
                tmp.add(dagstr)
                dp, comp = tmp.getComponent(0)
                if comp.isNull():
                    self._slist.add(dp, mergeWithExisting=merge)
                else:
                    self._slist.add((dp, comp), mergeWithExisting=merge)
        else:
            self._slist = api.MSelectionList()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{}'.format(list(self))

    def __getitem__(self, key):
        if isinstance(key, slice):
            raise TypeError('{} does not support slice.'
                            .format(self.__class__.__name__))

        mdag, mobj = self._slist.getComponent(len(self) - 1 if key == -1 else key)
        if mobj.isNull():
            return DagNode(mdag)
        return Component(mdag, mobj)

    def __len__(self):
        return self._slist.length()

    def __iter__(self):
        return iter(self._slist.getSelectionStrings())

    def __contains__(self, value):
        if isinstance(value, basestring):
            return value in self._slist.getSelectionStrings()
        if type(value) == tuple:
            return self._slist.hasItemPartly(*value)
        return self._slist.hasItem(value)

    def __eq__(self, other):
        return list(self) == list(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return bool(len(self))

    def __hash__(self):
        return hash(list(self))

    def index(self, value):
        return self._slist.getSelectionStrings().index(value)

    @classmethod
    def from_ls(cls, *args, **kwargs):
        """
        Constructs a :class:`SelectionList` from ``cmds.ls``.

        :param merge: If found components should be merged to one
            MObject.
        """
        if 'fl' in kwargs or 'flatten' in kwargs:
            merge = False
        else:
            merge = True
        return cls(cmds.ls(*args, **kwargs), merge)

    @classmethod
    def from_selection(cls):
        """
        Constructs a :class:`SelectionList` from
        ``api.OpenMaya.MGlobal.getActiveSelectionList()``.
        """
        return cls(api.MGlobal.getActiveSelectionList())

    @classmethod
    def from_ordered(cls, start=None, stop=None, step=None, **kwargs):
        """
        Construct a :class:`SelectionList` from ``cmds.ls(os=True)`` and
        return it.

        :param start: start of slice.
        :param stop: end of slice.
        :param step: slice steps.
        """
        return cls(cmds.ls(os=True, **kwargs)[slice(start, stop, step)], False)

    def append(self, value):
        """
        Appends a given dagpath to the end of the list.

        :param value: dagpath string, ``MObject``,
            ``(api.OpenMaya.MDatPath, api.OpenMaya.MObject)``
        """
        if isinstance(value, basestring):
            self._slist.add(value)
        elif isinstance(value, (DagNode, Component)):
            self._slist.add(value.node, mergeWithExisting=False)
        else:
            self._slist.add(value, mergeWithExisting=False)

    def extend(self, other, strategy=api.MSelectionList.kMergeNormal):
        """
        Extend list with other. s list with given

        :param other: :class:`SelectionList`, :class:`Component` or
            ``list, tuple, set`` of dagpath strings.
        :param strategy: ``api.OpenMaya.MSelectionList`` Merge strategy
        """
        try:
            if hasattr(other, '_slist'):
                self._slist.merge(other._slist, strategy)

            elif isinstance(other, api.MSelectionList):
                self._slist.merge(other)

            elif hasattr(other, '__len__'):
                if isinstance(other[0], Component):
                    for c in other:
                        self._slist.merge(c._slist)
                else:
                    try:
                        self._slist.merge(self.__class__(other)._slist)
                    except RuntimeError:
                        pass
        except TypeError:
            raise TypeError('Invalid type: {}'.format(type(other)))

    def copy(self):
        """
        Returns a copy of self.
        """
        return self.__class__(api.MSelectionList().copy(self._slist))

    # def toggle(self, other):
    #     """
    #     Toggles other :class:`SelectionList` objects with self.
    #     """
    #     self.extend(other, api.MSelectionList.kXORWithList)

    def remove(self, other):
        """
        Removes other :class:`SelectionList` objects from self.
        """
        self.extend(other, api.MSelectionList.kRemoveFromList)

    def pop(self, index=None):
        """
        pops given index from list.
        """
        index = len(self) - 1 if index is None else index
        value = self[index]
        self._slist.remove(index)
        return value

    __delitem__ = pop

    def itercomps(self):
        """
        Iterates over the :class:`SelectionList` :class:`Component`
        objects.
        """
        for idx in xrange(len(self)):
            yield Component(*self._slist.getComponent(idx))

    def iterdags(self):
        """
        Iterates over the :class:`SelectionList` :class:`DagNode`
        objects.
        """
        for idx in xrange(len(self)):
            yield DagNode(self._slist.getDagPath(idx))


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
        for a in oldapi.MSelectionMask.__dict__:
            if a.startswith('kSelect'):
                setattr(cls, a, oldapi.MSelectionMask.__dict__[a])
        return cls

    def __init__(self, mask=None):
        self._mask = mask or oldapi.MSelectionMask()

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
        return mgl.selectionMode()

    @property
    def typestr(self):
        return self.get_active_masks(internal=False, local=True)

    @classmethod
    def active(cls):
        """
        Return active selection mask.
        """
        mask = {
            mgl.kSelectObjectMode: mgl.objectSelectionMask(),
            mgl.kSelectComponentMode: mgl.componentSelectionMask(),
        }[mgl.selectionMode()]
        return cls(mask)

    @staticmethod
    def set_mode(kmode):
        """
        Set selection mode.

        :param kmode: internal selection mode pointer.
        """
        mgl.setSelectionMode(kmode)

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
        self._mask = oldapi.MSelectionMask()
        self.update()

    def update(self):
        """
        Set to be the active mask in Maya.
        """
        if self.mode == mgl.kSelectComponentMode:
            mgl.setComponentSelectionMask(self._mask)
        elif self.mode == mgl.kSelectObjectMode:
            mgl.setObjectSelectionMask(self._mask)


class OptionVar(collections.MutableMapping):
    """
    Dictionary class for accessing and modifying optionVars.

    Inspired by pymel OptionVarDict class found in pymel.core.language.
    """
    def __call__(self, *args, **kwargs):
        return cmds.optionVar(*args, **kwargs)

    def __contains__(self, key):
        return bool(cmds.optionVar(exists=key))

    def __getitem__(self, key):
        if key not in self:
            raise KeyError()

        val = cmds.optionVar(q=key)
        if isinstance(val, (list)):
            val = OptionVarList(val, key)
        return val

    def __setitem__(self, key, val):
        if isinstance(val, basestring):
            return cmds.optionVar(stringValue=(key, val))

        elif isinstance(val, (int, bool)):
            return cmds.optionVar(intValue=(key, val))

        elif isinstance(val, float):
            return cmds.optionVar(floatValue=(key, val))

        elif isinstance(val, (set, list, tuple, xrange)):
            if len(val) == 0:
                return cmds.optionVar(ca=True)

            seq_type = type(iter(val).next())
            if issubclass(seq_type, basestring):
                flag = 'stringValue'
            elif issubclass(seq_type, int):
                flag = 'intValue'
            elif issubclass(seq_type, float):
                flag = 'floatValue'
            else:
                raise TypeError(
                    '{0!r} is unsupported, valid types are; '
                    'strings, ints and floats.'.format(seq_type)
                )
            flag += 'Append'
            for each in val:
                cmds.optionVar(**{flag: (key, each)})

    def __len__(self):
        return self.keys()

    def pop(self, key):
        val = cmds.optionVar(q=key)
        cmds.optionVar(remove=key)
        return val

    __delitem__ = pop

    def iterkeys(self):
        return iter(self.keys())

    __iter__ = iterkeys

    def keys(self):
        return cmds.optionVar(list=True)


class OptionVarList(collections.Sequence):

    def __init__(self, items, key):
        self.items = items
        self.key = key
        self.type = type(items[0])
        if self.type in (unicode, str):
            self.type = basestring

    def __repr__(self):
        return '{}({}({}))'.format(self.__class__.__name__, self.key,
                                   self.items)

    def __str__(self):
        return '{}'.format(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

    def __reversed__(self):
        cmds.optionVar(clearArray=self.key)
        for i in reversed(self.items):
            self.append(i)

    def pop(self, idx):
        val = self.items.pop(idx)
        cmds.optionVar(removeFromArray=(self.key, idx))
        return val

    def clear(self):
        cmds.optionVar(clearArray=self.key)

    def append(self, val):
        """
        Appends given value to end of optionVar list.
        """
        if not isinstance(val, self.type):
            raise TypeError('Valid type for {} is {}, value given was: {}'
                            .format(self.key, self.type, type(val)))

        if isinstance(val, int):
            cmds.optionVar(intValueAppend=(self.key, val))
        elif isinstance(val, basestring):
            cmds.optionVar(stringValueAppend=(self.key, val))
        elif isinstance(val, float):
            cmds.optionVar(floatValueAppend=(self.key, val))
        else:
            raise TypeError('Valid type for {} is {}'.format(self.key,
                            self.type))
        self.items = cmds.optionVar(q=self.key)


class MelGlobals(collections.Mapping):

    MELTYPES = {'string': str, 'int': int, 'float': float,
                'vector': api.MVector}
    TYPE_MAP = {}
    key_values = {}

    def __init__(self, *args, **kwargs):
        super(MelGlobals, self).__init__(*args, **kwargs)
        self._globals = mel.eval('env;')

    def __getitem__(self, key):
        try:
            return self.key_values[key]
        except KeyError:
            r = self.get(key)
            self.key_values[key] = r
            return r

    def __iter__(self):
        for var in self._globals:
            if var.startswith('$'):
                var = var[1:]
            yield var

    def __len__(self):
        return len(self._globals)

    def _format_var(self, var):
        if not var.startswith('$'):
            var = '$' + var
        if var.endswith('[]'):
            var = var[:-2]
        return var

    def _get_var_type(self, var):
        try:
            return self.TYPE_MAP[var]
        except KeyError:
            pass

        t = mel.eval('whatIs "{}"'.format(var)).split()
        if t[0].startswith('Unknown'):
            raise KeyError('{}'.format(var))

        if len(t) == 2 and t[1].startswith('variable'):
            self.TYPE_MAP[var] = t[0]
            return t[0]
        raise TypeError('Cannot determine type of {}'.format(var))

    def _get_declare(self, type, var):
        if type.endswith('[]'):
            type = type[:-2]
            var += '[]'
        return 'global {} {}'.format(type, var)

    def get(self, var, type=None):

        var = self._format_var(var)
        if type is None:
            type = self._get_var_type(var)

        if type.endswith('[]'):
            proc_name = 'mampy_get_global_' + var[1:].replace('[]', 'array')
        else:
            proc_name = 'mampy_get_global_' + type

        try:
            global_declare = self._get_declare(type, var)
            cmd = textwrap.dedent('''
                global proc {type} {proc_name}()
                {{
                    {global_declare};
                    return {var};
                }}
                {proc_name}()
            '''.format(**locals()))
            result = mel.eval(cmd)
        except RuntimeError:
            raise RuntimeError('{} is an undeclared variable.'.format(var))

        try:
            if type.endswith('[]'):
                return tuple(mel.eval(cmd))
            else:
                return self.MELTYPES[type](mel.eval(cmd))
        except RuntimeError:
            raise RuntimeError('{}'.format(cmd))


if __name__ == '__init__':
    pass
