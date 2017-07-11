
from Qt import QtCompat, QtWidgets
import maya.OpenMayaUI as omui


def get_maya_main_window():
    """
    Get the main Maya window as a QtWidgets.QMainWindow instance
    @return: QtWidgets.QMainWindow instance of the top level Maya windows
    """
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return QtCompat.wrapInstance(long(ptr), QtWidgets.QWidget)


def get_qt_object(maya_name):
    """
     Convert a Maya ui path to a Qt object @param maya_name: Maya UI Path to
     convert (Ex:
     "scriptEditorPanel1Window|TearOffPane|scriptEditorPanel1|testButton" )
     @return: PyQt representation of that object
    """
    ptr = omui.MQtUtil.findControl(maya_name)
    if ptr is None:
        ptr = omui.MQtUtil.findLayout(maya_name)
    if ptr is None:
        ptr = omui.MQtUtil.findMenuItem(maya_name)
    if ptr is not None:
        return QtCompat.wrapInstance(long(ptr), QtWidgets.QObject)
