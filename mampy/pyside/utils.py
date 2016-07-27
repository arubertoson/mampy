import pysideuic
import xml.etree.ElementTree as xml
from cStringIO import StringIO

import shiboken
from PySide import QtGui, QtCore

import maya.OpenMayaUI as apiUI

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


def get_maya_main_window():
    """
    Get the main Maya window as a QtGui.QMainWindow instance
    @return: QtGui.QMainWindow instance of the top level Maya windows
    """
    ptr = apiUI.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr), QtGui.QWidget)


def loadUiType(ui_file):
        """
        Pyside lacks the "loadUiType" command, so we have to convert the ui file
        to py code in-memory first and then execute it in a special frame to
        retrieve the form_class.

        Usage:

            >>> class SomeDialog(loadUiType('some_dialog.ui')):
            >>>     def __init__(self, *args, **kwargs):
            >>>         super(SomeDialog, self).__init__(*args, **kwargs)

        """
        parsed = xml.parse(ui_file)
        widget_class = parsed.find('widget').get('class')
        form_class = parsed.find('class').text

        with open(ui_file, 'r') as f:
            o = StringIO()
            frame = {}

            pysideuic.compileUi(f, o, indent=0)
            pyc = compile(o.getvalue(), '<string>', 'exec')
            exec pyc in frame

            # Fetch the base_class and form class based on their type in the xml
            # from designer
            form_class = frame['Ui_%s' % form_class]
            base_class = eval('QtGui.%s' % widget_class)
        return type('PySideUI', (form_class, base_class), {})


def load_ui(fname):
    """Read Qt Designer .ui `fname`
    Args:
        fname (str): Absolute path to .ui file
    Usage:
        >> from Qt import load_ui
        >> class MyWindow(QtWidgets.QWidget):
        ..   fname = 'my_ui.ui'
        ..   self.ui = load_ui(fname)
        ..
        >> window = MyWindow()
    """

    from PySide import QtUiTools
    return QtUiTools.QUiLoader().load(fname)


def get_qt_object(maya_name):
    """
    Convert a Maya ui path to a Qt object
    @param maya_name: Maya UI Path to convert (Ex: "scriptEditorPanel1Window|TearOffPane|scriptEditorPanel1|testButton" )
    @return: PyQt representation of that object
    """
    ptr = apiUI.MQtUtil.findControl(maya_name)
    if ptr is None:
        ptr = apiUI.MQtUtil.findLayout(maya_name)
    if ptr is None:
        ptr = apiUI.MQtUtil.findMenuItem(maya_name)
    if ptr is not None:
        return wrapinstance(long(ptr), QtCore.QObject)


def wrapinstance(ptr, base=None):
    """
    Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)

    :param ptr: Pointer to QObject in memory
    :type ptr: long or Swig instance
    :param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
    :type base: QtGui.QWidget
    :return: QWidget or subclass instance
    :rtype: QtGui.QWidget
    """
    if ptr is None:
        return None
    ptr = long(ptr)  # Ensure type
    if globals().has_key('shiboken'):
        if base is None:
            qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
            metaObj = qObj.metaObject()
            cls = metaObj.className()
            superCls = metaObj.superClass().className()
            if hasattr(QtGui, cls):
                base = getattr(QtGui, cls)
            elif hasattr(QtGui, superCls):
                base = getattr(QtGui, superCls)
            else:
                base = QtGui.QWidget
        return shiboken.wrapInstance(long(ptr), base)
    elif globals().has_key('sip'):
        base = QtCore.QObject
        return sip.wrapinstance(long(ptr), base)
    else:
        return None


class ListExample(MayaQWidgetDockableMixin, QtGui.QMainWindow):

    def __init__(self, parent=get_maya_main_window()):
        super(ListExample, self).__init__(parent)

        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        fname = 'C:\\pytest.ui'
        self.setWindowTitle('Cool Bro')
        self.setObjectName('TexelDensity')

        self.ui = load_ui(fname)
        self.ui.get_texture_size_button.clicked.connect(self.hello)

        self.setCentralWidget(self.ui)

    def hello(self):
        print ('hello')


if __name__ == "__main__":
    if cmds.window('TexelDensity', q=True, exists=True): cmds.deleteUI('TexelDensity')
    if cmds.dockControl('MayaWindow|TexelDensity', q=True, exists=True): cmds.deleteUI('MayaWindow|TexelDensity')
    le = ListExample()

