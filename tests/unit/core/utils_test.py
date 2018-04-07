"""
Test for mampy.core.utils
"""
import pytest

from maya import cmds
from maya.api import OpenMaya as om
from mampy.core import utils


def test_get_maya_component_from_input_WithStringObject_ReturnMayaComponent(
        maya_dagpath):
    with maya_dagpath() as dagpath:
        strcomp = str(dagpath) + '.f[*]'
        comp = utils.get_maya_component_from_input(strcomp)
    assert comp[1].apiType() == om.MFn.kMeshPolygonComponent


def test_get_maya_dagpath_from_input_WithStringObject_ReturnMayaDagPath(
        maya_dagpath):
    with maya_dagpath() as dagpath:
        dagpath = utils.get_maya_dagpath_from_input(str(dagpath))
        assert isinstance(dagpath, om.MDagPath)


def test_get_maya_strlist_from_iterable_StringElementList_ReturnMSelectionListWithElements(
        daglist):
    strlist = daglist.getSelectionStrings()
    mlist = utils.get_maya_strlist_from_iterable(strlist)
    assert mlist.length() == daglist.length()


def test_is_track_order_set_MayaCmds_ReturnFalse():
    assert not utils.is_track_order_set()


def test_is_track_order_set_MayaCmds_ReturnTrue():
    cmds.selectPref(trackSelectionOrder=True)
    assert utils.is_track_order_set()


@pytest.mark.parametrize('input,expected', [({
    'fl': True
}, True), ({
    'flatten': True,
    'something': False
}, True), ({
    'sl': True
}, False), ({
    'os': True,
    'sl': True
}, True), ({
    'objects': True,
    'orderedSelection': True
}, True)])
def test_need_ordered_selection_set_KeyWordArguments_ReturnExpected(
        input, expected):
    assert utils.need_ordered_selection_set(input) == expected


def test_itermayalist_MSelectionList_ReturnGenerator(daglist):
    import types
    iterator = utils.itermayalist(daglist)
    assert isinstance(iterator, types.GeneratorType)
