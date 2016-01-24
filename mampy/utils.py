"""
This module provides utility functions that are useful for general maya
script development. These can also be useful for external purposes.
"""
import sys
import logging
import textwrap
import functools
import collections

from maya import cmds
from maya import mel

import maya.OpenMaya as oldapi
import maya.api.OpenMaya as api

from PySide import QtGui
import mampy
from mampy.packages.mvp import Viewport
from mampy.packages.contextlib2 import ContextDecorator

__all__ = ['get_outliner_index', 'history_chunk', 'select_keep',
           'get_object_under_cursor',  # 'object_selection_mode'
           'get_objects_in_view', 'OptionVar', 'DraggerCtx', 'MelGlobals',
           'HistoryList']


logger = logging.getLogger(__name__)
EPS = sys.float_info.epsilon


def script_job_exists(jobnum, event):
    """
    This is too general of a function, should probablyh be moved to mampy.

    .. todo:: move to mampy
    """
    if not cmds.scriptJob(exists=jobnum):
        return False
    for i in cmds.scriptJob(lj=True):
        if i.startswith(str(jobnum)) and str(event) in i:
            return True
    return False


def get_outliner_index(dagnode):
    """
    Return the current index of the given node in the outliner.
    """
    if dagnode.is_root():
        return mampy.ls(l=True, assemblies=True).index(dagnode.name)
    else:
        outliner = mampy.ls(dag=True, tr=True, l=True)
        parent = dagnode.get_parent()
        return outliner.index(dagnode.name) - outliner.index(parent.name)


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
    Context Decorator that restore selection after call.
    """
    def __enter__(self):
        self.slist = cmds.ls(sl=True)
        self.hlist = cmds.ls(hl=True)

        if self.hlist:
            cmds.hilite(self.hlist, toggle=True)

    def __exit__(self, *args):
        cmds.select(self.slist, r=True)
        if self.hlist:
            cmds.hilite(self.hlist)


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


class object_mode(ContextDecorator):
    """
    Context Decorator that makes call execute in Maya object mode.
    """
    def __enter__(self):
        self.object_mode = cmds.selectMode(q=True, object=True)
        if not self.object_mode:
            cmds.selectMode(object=True)
            self.compk = get_active_flags_in_mask(object=False)

        self.objk = get_active_flags_in_mask(object=True)
        # make sure all objects can be selected.
        cmds.selectType(allObjects=True)

    def __exit__(self, *args):
        # Restore object selection mask.
        cmds.selectType(**self.objk)

        # restore mode
        if not self.object_mode:
            cmds.selectMode(component=True)
            cmds.selectType(**self.compk)


@select_keep()
def get_object_under_cursor():
    """
    Return selectable object under cursor.
    """
    view = Viewport.active()
    cursor_pos = view.widget.mapFromGlobal(QtGui.QCursor.pos())

    # Get screen object
    with object_mode():
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
    with object_mode():
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


class DraggerCtx(object):
    """
    Base class for creating draggerContext in Maya.

    :param name: string name of context.
    :param \*\*kwargs: all optional parameters for draggerContext
    """

    _context_properties = [
        'image1', 'i1', 'i2', 'image2', 'image3',
        'i3', 'prePressCommand', 'ppc', 'holdCommand', 'hc',
        'anchorPoint', 'ap', 'dragPoint', 'dp', 'projection', 'pr',
        'plane', 'pl', 'space', 'sp', 'modifier', 'mo', 'button', 'bu',
        'cursor', 'cur', 'drawString', 'ds', 'undoMode', 'um',
        'stepsCount', 'sc', 'snapping', 'snp', 'currentStep', 'cs'
    ]

    def __init__(self, name, **kwargs):
        self.name = name
        if not cmds.draggerContext(self.name, exists=True):
            self.name = cmds.draggerContext(name)

        cmds.draggerContext(
            self.name,
            edit=True,
            pressCommand=self.press,
            dragCommand=self.drag,
            releaseCommand=self.release,
            inz=self.setup,
            fnz=self.tear_down,
            **kwargs
        )
        self.context = functools.partial(cmds.draggerContext, self.name)

    def __getattr__(self, name):
        if name in self._context_properties:
            return self.context(**{'query': True, name: True})

    def __setattr__(self, name, value):
        if name in self._context_properties:
            self.context(**{'edit': True, name: value})
        else:
            super(DraggerCtx, self).__setattr__(name, value)

    def _get_modifiers(self):
        """
        Return pressed modifiers.
        """
        from PySide import QtGui, QtCore
        qapp = QtGui.qApp
        shift_mod = qapp.keyboardModifiers() & QtCore.Qt.ShiftModifier
        ctrl_mod = qapp.keyboardModifiers() & QtCore.Qt.ControlModifier
        if (ctrl_mod == QtCore.Qt.ControlModifier and
                shift_mod == QtCore.Qt.ShiftModifier):
            return 3
        elif ctrl_mod == QtCore.Qt.ControlModifier:
            return 2
        elif shift_mod == QtCore.Qt.ShiftModifier:
            return 1
        else:
            return 0

    def setup(self):
        """
        Run on tool start.
        """

    def tear_down(self):
        """
        Run on tool drop.
        """

    def press(self):
        """
        Called on press.
        """
        cmds.undoInfo(openChunk=True)
        try:
            button = 0 if self.button == 1 else 1
            dispatch = {
                0: [self.press_left, self.press_shift_middle],
                1: [self.press_shift_left, self.press_shift_middle],
                2: [self.press_ctrl_left, self.press_ctrl_middle],
                3: [self.press_ctrl_shift_left, self.press_ctrl_shift_middle],
            }[self._get_modifiers()][button]
        except KeyError:
            raise KeyError('Something went wrong.')
        dispatch()

    def press_left(self):
        pass

    def press_middle(self):
        pass

    def press_ctrl_left(self):
        pass

    def press_ctrl_middle(self):
        pass

    def press_shift_left(self):
        pass

    def press_shift_middle(self):
        pass

    def press_ctrl_shift_left(self):
        pass

    def press_ctrl_shift_middle(self):
        pass

    def drag(self):
        """
        Called during drag.
        """
        try:
            button = 0 if self.button == 1 else 1
            dispatch = {
                0: [self.drag_left, self.drag_middle],
                1: [self.drag_shift_left, self.drag_shift_middle],
                2: [self.drag_ctrl_left, self.drag_ctrl_middle],
                3: [self.drag_ctrl_shift_left, self.drag_ctrl_shift_middle],
            }[self._get_modifiers()][button]
        except KeyError:
            raise KeyError('Something went wrong.')
        dispatch()
        cmds.refresh()

    def drag_left(self):
        pass

    def drag_middle(self):
        pass

    def drag_ctrl_left(self):
        pass

    def drag_ctrl_middle(self):
        pass

    def drag_shift_left(self):
        pass

    def drag_shift_middle(self):
        pass

    def release(self):
        """
        Called during release
        """
        cmds.undoInfo(closeChunk=True)

    def run(self):
        """
        Start tool.
        """
        cmds.setToolTo(self.name)


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


class HistoryList(object):
    """
    Stores current jump history
    """
    LIST_LIMIT = 20
    LIST_TRIMMED_SIZE = 15

    def __init__(self):
        self.history_list = []

        self.current_item = 0
        self.key_counter = 0

    def __len__(self):
        return len(self.history_list)

    def push_selection(self, elements):
        """
        Push the current selection into this history.
        """
        if not elements:
            return

        self.clear_history_after_current()

        selected_elements = set(list(elements))
        if self.history_list != []:
            first_item = self.history_list[-1]
            if first_item == selected_elements:
                return

        # set the selected item as the current item
        self.history_list.append(selected_elements)
        self.trim_selections()

        logger.debug(self.history_list)

    def jump_back(self, active_elmenets):
        """
        Return element behind of active element in history_list.
        """
        if self.current_item == 0:
            self.push_selection(active_elmenets)
            self.current_item = -1

        if self.current_item == -len(self.history_list):
            return None

        self.current_item -= 1
        return list(self.history_list[self.current_item])

    def jump_forward(self, active_elmenets):
        """
        Return element in front of active element in history_list.
        """
        if self.history_list == []:
            return None

        # Already at the front
        if self.current_item >= -1:
            return None

        self.current_item += 1
        return list(self.history_list[self.current_item])

    def remove_element(self, element):
        i = 0
        while (i > -len(self.history_list)):
            i -= 1
            if self.history_list[i] == element:
                del self.history_list[i]
                if self.current_item <= i:
                    self.current_item += 1

    def clear_history_after_current(self):
        if self.current_item == 0:
            return
        del self.history_list[self.current_item + 1:]
        self.current_item = 0

    def trim_selections(self):
        """
        Trim everything too old when reaching list limit.
        """
        if len(self.history_list) > self.LIST_LIMIT:
            del self.history_list[:len(self.history_list)-self.LIST_TRIMMED_SIZE]


if __name__ == '__main__':
    print get_object_under_cursor()
