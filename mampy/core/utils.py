# -*- coding: utf-8 -*-
"""
mampy.core.utils

This module contains helper functions for mampy.core objects.
"""
import itertools
from abc import ABCMeta, abstractmethod

from maya import cmds
from maya.api import OpenMaya as om


class IMayaStringList(object):
    """ Interface that implements the represenation of a Maya Object as a
    list of strings.

    """
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractmethod
    def cmdslist(self, index=None):
        pass


def get_maya_component_from_input(input):
    return om.MSelectionList().add(input).getComponent(0)


def get_maya_dagpath_from_input(input):
    return om.MSelectionList().add(input).getDagPath(0)


def get_maya_strlist_from_iterable(string_elements, merge):
    mlist = om.MSelectionList()
    for each in string_elements:
        mlist.add(each, merge)
    return mlist


def is_track_order_set():
    return cmds.selectPref(q=True, trackSelectionOrder=True)


def need_ordered_selection_set(kw):
    return any(i in kw for i in ('fl', 'flatten', 'os', 'orderedSelection'))


def itermayalist(mlist):
    it = om.MItSelectionList(mlist)
    while not it.isDone():
        yield it
        it.next()
