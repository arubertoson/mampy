"""
Tests for mampy.core.selectionlist -> ComponentList
"""
import contextlib
import copy
from random import randint

import pytest

from maya import cmds
import maya.api.OpenMaya as om

from mampy.core.selectionlist import ComponentList


def test_empty_componentlist():
    assert not ComponentList()


def test_componentlist_init_with_string_list_fail(xcubes):
    with pytest.raises(TypeError):
        assert not ComponentList([cube[0] for cube in xcubes(5)])


def test_componentlist_init_with_maya_MSelectionList_fail(xcubes):
    msl = om.MSelectionList()
    for each in [cube[0] for cube in xcubes(5)]:
        msl.add(each)
    assert not ComponentList(msl)


def test_componentlist_init_with_maya_MDagPath_MObject_fail(xcubes):
    msl = om.MSelectionList()
    for each in [cube[0] for cube in xcubes(5)]:
        msl.add(each)

    with pytest.raises(TypeError):
        assert not ComponentList(
            [msl.getComponent(idx) for idx in xrange(msl.length())]
        )


def test_componentlist_init_with_string_list_success(xcomponents):
    assert ComponentList([comp for comp in xcomponents(randint(1, 10))])


def test_componentlist_init_with_maya_MSelectionList_sucess(xcomponents):
    msl = om.MSelectionList()
    for each in xcomponents(randint(1, 10)):
        msl.add(each)
    assert ComponentList(msl)


def test_componentlist_init_with_maya_MDagPath_MObject_success(xcomponents):
    msl = om.MSelectionList()
    for each in xcomponents(randint(1, 10)):
        msl.add(each)

    assert ComponentList(
        [msl.getComponent(idx) for idx in xrange(msl.length())]
    )


def test_componentlist_len(xcomponents):
    assert len(ComponentList(list(xcomponents(10)))) == 10


def test_componentlist_getitem(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    assert complist[0]


def test_componentlist_getitem_returns_component_object(xcomponents):
    from mampy.core.components import AbstractComponent
    complist = ComponentList(list(xcomponents(10)))
    assert isinstance(complist[0], AbstractComponent)


def test_componentlist_getitem_slice(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    slice_ = complist[2:4]
    assert len(slice_) == 2


def test_componentlist_getitem_slice_returns_new_componentlist(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    slice_ = complist[2:4]
    assert isinstance(slice_, ComponentList)


def test_componentlist_equality_equals(xcomponents):
    component = list(xcomponents(10))
    list1 = ComponentList(component)
    list2 = ComponentList(component)
    assert list1 == list2


def test_componentlist_equality_len_not_equals(xcomponents):
    list1 = ComponentList(list(xcomponents(5)))
    list2 = ComponentList(list(xcomponents(10)))
    assert list1 != list2


def test_componentlist_equality_not_equals(xcomponents):
    list1 = ComponentList(list(xcomponents(10)))
    list2 = ComponentList(list(xcomponents(10)))
    assert list1 != list2


def test_componentlist_append_string_component(xcomponents):
    comp = cmds.ls(list(xcomponents(1))).pop()
    complist = ComponentList()
    complist.append(comp)
    assert str(complist[0]) == comp


def test_append_to_complist_with_maya_component(maya_component):
    complist = ComponentList()
    with maya_component() as comp:
        complist.append(comp)
        assert complist._slist.hasItem(comp)


def test_append_to_complist_with_dagpath_raising_typeerror(maya_dagpath):
    complist = ComponentList()
    with maya_dagpath() as dagp:
        with pytest.raises(TypeError):
            complist.append(dagp)
            assert len(complist) == 0


# TODO: Missing test for mampy component append


def test_componentlist_extend_with_mselectionlist(xcomponents):
    list1 = ComponentList(list(xcomponents(10)))
    list2 = ComponentList(list(xcomponents(10)))
    list1.extend(list2)
    assert len(list1) == 20


def test_componentlist_extend_with_stringlist(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    complist.extend(list(xcomponents(10)))
    assert len(complist) == 20


# TODO: MIssing test for mampy component extend


def test_componentlist_cache_getitem(maya_component):
    complist = ComponentList()
    with maya_component() as comp:
        complist.append(comp)
        assert not complist._cache
        t = complist[0]
        assert complist._cache


def test_componentlist_cache_iter(maya_component):
    complist = ComponentList()
    with maya_component() as comp:
        complist.append(comp)
        assert not complist._cache
        t = list(complist)
        assert complist._cache


def test_componentlist_contains(maya_component):
    complist = ComponentList()
    with maya_component() as comp:
        complist.append(comp)
        assert comp in complist


# TODO: Missing contains test with mampy Component object


def test_componentlist_iter(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    assert list(complist)


def test_componentlist_iter_len(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    assert len(list(complist)) == len(complist)


def test_componentlist_copy(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    copylist = copy.copy(complist)
    assert complist == copylist


def test_componentlist_copy_cache(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    copylist = copy.copy(complist)
    assert complist._cache == copylist._cache


def test_componentlist_remove(maya_component):
    with maya_component() as comp:
        complist = ComponentList()
        complist.append(comp)
        print(len(complist))
        complist.remove(0)
        assert not (complist)


def test_componentlist_pop(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    last = complist[-1]
    assert complist.pop() == last


def test_componentlist_pop_index(xcomponents):
    complist = ComponentList(list(xcomponents(10)))
    indexed = complist[5]
    assert complist.pop(5) == indexed


def test_componentlist_replace_with_maya_dagpath(xcomponents, maya_dagpath):
    complist = ComponentList(list(xcomponents(10)))
    indexed = complist[5]
    with pytest.raises(TypeError):
        with maya_dagpath() as cube:
            complist.replace(5, cube)
            assert complist[5] == cube


def test_componentlist_replace_with_maya_component(xcomponents, maya_component):
    complist = ComponentList(list(xcomponents(10)))
    from mampy.core.components import SingleIndexComponent
    with maya_component() as comp:
        # TODO: Component assert needs to be through MFnComponent as the
        # other means seems to be ineffective - refactor Component
        complist.replace(0, comp)
        test = om.MFnComponent(comp[1])
        assert test.isEqual(comp[1])


# TODO: Test with mampy Component


def test_componentlist_replace_maya_component(xcomponents, maya_component):
    complist = ComponentList(list(xcomponents(10)))


def test_componentlist_cmdslist(xcomponents):
    strcomplist = set(cmds.ls(list(xcomponents(10))))
    assert set(ComponentList(strcomplist).cmdslist()) == strcomplist
