"""
This module provides utility functions that are useful for general maya
script development. These can also be useful for external purposes.
"""
import collections

from maya import cmds
import maya.OpenMaya as oldapi
from maya.OpenMaya import MGlobal as mgl

from PySide import QtGui
from mampy.packages.mvp import Viewport
from mampy.packages.contextlib2 import ContextDecorator, contextmanager


__all__ = ['history_chunk', 'select_keep', 'object_selection_mode',
           'get_object_under_cursor', 'get_objects_in_view',
           'OptionVar', 'SelectionMask']


class history_chunk(ContextDecorator):
    """
    History chunk decorator.

    Wraps function inside a history chunk enabling undo chunks to be
    created on python functions.
    """
    def __enter__(self):
        cmds.undoInfo(openChunk=True)

    def __exit__(self, type, value, traceback):
        cmds.undoInfo(closeChunk=True)
        if traceback:
            cmds.undo()


class select_keep(ContextDecorator):
    """
    Selection decorator.

    Wraps function to record the current selection and then restore it
    when function returns.
    """
    def __enter__(self):
        self.slist = oldapi.MSelectionList()
        self.hlist = oldapi.MSelectionList()
        self.empty = oldapi.MSelectionList()

        oldapi.MGlobal.getHiliteList(self.hlist)
        oldapi.MGlobal.getActiveSelectionList(self.slist)
        oldapi.MGlobal.setActiveSelectionList(self.empty)
        if self.hlist:
            oldapi.MGlobal.setHiliteList(self.empty)

        string_list = []
        self.slist.getSelectionStrings(string_list)
        return string_list

    def __exit__(self, *exc):
        if self.hlist:
            oldapi.MGlobal.setHiliteList(self.hlist)
            oldapi.MGlobal.setActiveSelectionList(self.slist)


@contextmanager
def object_selection_mode():
    """
    Context that executes code in object selection mode and restore
    mode after execution.
    """
    smode = oldapi.MGlobal.kSelectObjectMode
    oldapi.MGlobal.setSelectionMode(smode)

    hlist = oldapi.MSelectionList()
    oldapi.MGlobal.getActiveSelectionList(hlist)
    if not hlist.isEmpty():
        smode = oldapi.MGlobal.kSelectComponentMode
    try:
        yield smode
    except:
        raise
    finally:
        oldapi.MGlobal.setSelectionMode(smode)


@select_keep()
def get_object_under_cursor():
    """
    Return selectable object under cursor.
    """
    view = Viewport.active()
    cursor_pos = view.widget.mapFromGlobal(QtGui.QCursor.pos())

    # Get screen object
    with object_selection_mode():
        oldapi.MGlobal.selectFromScreen(
            cursor_pos.x(),
            view.widget.height()-cursor_pos.y(),  # Maya counts from below
            oldapi.MGlobal.kReplaceList,
            oldapi.MGlobal.kSurfaceSelectMethod
            )
    objects = oldapi.MSelectionList()
    oldapi.MGlobal.getActiveSelectionList(objects)

    # return as object string
    under_cursor = []
    objects.getSelectionStrings(under_cursor)
    try:
        return under_cursor.pop()
    except IndexError:
        return None


@select_keep()
def get_objects_in_view(objects=True):
    """
    Return selectable objects on screen.
    """
    view = Viewport.active()
    with object_selection_mode():
        oldapi.MGlobal.selectFromScreen(
            0,
            0,
            view.widget.width(),
            view.widget.height(),
            oldapi.MGlobal.kReplaceList
            )
    objects = oldapi.MSelectionList()
    oldapi.MGlobal.getActiveSelectionList(objects)

    # return the object string list
    fromScreen = []
    objects.getSelectionStrings(fromScreen)
    return fromScreen


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
            raise KeyError(key)

        val = cmds.optionVar(q=key)
        if isinstance(val, list):
            val = OptionVarList(val, key)
        return val

    def __setitem__(self, key, val):
        if isinstance(val, basestring):
            return cmds.optionVar(stringValue=[key, val])

        elif isinstance(val, (int, bool)):
            return cmds.optionVar(intValue=[key, int(val)])

        elif isinstance(val, float):
            return cmds.optionVar(floatValue=[key, val])

        elif isinstance(val, (set, list, tuple, xrange)):
            if len(val) == 0:
                return cmds.optionVar(clearArray=key)

            sequencetype = type(iter(val).next())
            if issubclass(sequencetype, basestring):
                flag = 'stringValue'
            elif issubclass(sequencetype, int):
                flag = 'intValue'
            elif issubclass(sequencetype, float):
                flag = 'floatValue'
            else:
                raise TypeError(
                    '{0!r} is unsupported, valid types are; '
                    'strings, ints and floats.'.format(sequencetype)
                )

            flag += 'Append'
            for each in val:
                cmds.optionVar(**{flag: [key, each]})

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def pop(self, key):
        val = cmds.optionVar(q=key)
        cmds.optionVar(remove=key)
        return val

    __delitem__ = pop

    def keys(self):
        return cmds.optionVar(list=True)


class OptionVarList(tuple):

    def __new__(cls, val, key):
        return tuple.__new__(cls, val)

    def __init__(self, val, key):
        self.key = key

    def append(self, val):
        """Appends given value to end of optionVar list."""
        if isinstance(val, basestring):
            return cmds.optionVar(stringValueAppend=[self.key, val])

        elif isinstance(val, int):
            return cmds.optionVar(intValueAppend=[self.key, val])

        elif isinstance(val, float):
            return cmds.optionVar(floatValueAppend=[self.key, val])

        else:
            raise TypeError(
                'Unsupported datatype. Valid types; strings, ints and floats.'
            )


class SelectionMask(object):
    """
    Selection mask class for accessing and chaning selection mask
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


if __name__ == '__main__':
    print get_object_under_cursor()
