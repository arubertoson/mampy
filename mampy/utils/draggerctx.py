"""
"""
import functools
from abc import ABCMeta, abstractmethod

from maya import cmds


class AbstractDraggerCtx(object):
    """
    Base class for creating draggerContext in Maya.

    :param name: string name of context.
    :param \*\*kwargs: all optional parameters for draggerContext
    """
    __metaclass__ = ABCMeta

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
            super(AbstractDraggerCtx, self).__setattr__(name, value)

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

    @abstractmethod
    def setup(self):
        """
        Run on tool start.
        """

    @abstractmethod
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
