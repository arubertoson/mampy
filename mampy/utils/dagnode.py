"""
"""
from PySide import QtGui

from maya import OpenMaya as oapi

from mampy.packages.mvp import Viewport
from .decorators import object_mode, select_keep


@select_keep()
def get_object_under_cursor():
    """
    Return selectable object under cursor
    """
    view = Viewport.active()
    cursor_pos = view.widget.mapFromGlobal(QtGui.QCursor.pos())

    with object_mode():
        oapi.MGlobal.selectFromScreen(
            cursor_pos.x(),
            view.widget.height() - cursor_pos.y(),  # Maya counts from below
            oapi.MGlobal.kReplaceList,
            oapi.MGlobal.kSurfaceSelectMethod
        )
        objects = oapi.MSelectionList()
        oapi.MGlobal.getActiveSelectionList(objects)

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
        oapi.MGlobal.selectFromScreen(
            0,
            0,
            view.widget.width(),
            view.widget.height(),
            oapi.MGlobal.kReplaceList
        )
        objects = oapi.MSelectionList()
        oapi.MGlobal.getActiveSelectionList(objects)

    # return the object string list
    from_screen = []
    objects.getSelectionStrings(from_screen)
    try:
        return from_screen.pop()
    except IndexError:
        return None
