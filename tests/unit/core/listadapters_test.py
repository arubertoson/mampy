# -*- coding: utf-8 -*-
"""
Tests for mampy.core.listadapters
"""
import itertools
import pytest

from mampy.core import listadapters as adapters
from mampy.core.exceptions import OrderedSelectionsNotSet

from maya import cmds
from maya.api import OpenMaya as om


def singleindexed(comp):
    return om.MFnSingleIndexedComponent(comp[1])


class ComponentFactoryMock(object):

    def __init__(self, comp):
        self.dagpath, self.mobject = comp

    @property
    def node(self):
        return (self.dagpath, self.mobject)


class TestComponentList(object):
    """ComponentList Tests

    ComponentList tests are also in charge of tests directed towards general
    functionality of AbstractMListAdapter and AbstractMListSequence.
    """

    def test__init__WithoutParameters_ReturnEmptyComponentList(self):
        adapters.ComponentList()

    def test__is_valid__WithComponentList_ReturnTrue(self, complist):
        nonempty_list = adapters.ComponentList()
        nonempty_list._mlist = complist
        assert nonempty_list.is_valid()

    def test__is_valid__WithDagpathList_ReturnFalse(self, daglist):
        nonempty_list = adapters.ComponentList()
        nonempty_list._mlist = daglist
        assert not nonempty_list.is_valid()

    def test__init__WithoutParameters_ReturnEmptyMListFactory(self):
        empty_list = adapters.ComponentList()
        assert not empty_list

    def test__init__WithEmptyMSelectionList_ReturnEmptyMListFactory(self):
        empty_list = adapters.ComponentList(om.MSelectionList())
        assert not empty_list

    def test__init__WithListOfComponents_ReturnValidObjectWithComponents(
            self, complist):
        nonempty_list = adapters.ComponentList(complist)
        assert nonempty_list

    def test__nonzero__WithEmptyComponentList_ReturnFalse(self):
        empty_list = adapters.ComponentList()
        assert not empty_list

    def test__nonzero__WithNonEmptyComponentlist_ReturnTrue(self, complist):
        nonempty_list = adapters.ComponentList(complist)
        assert nonempty_list

    def test__len__WithComponentList_ReturnExpectedAmount(self, complist):
        nonempty_list = adapters.ComponentList(complist)
        assert len(nonempty_list) == complist.length()

    def test__contains__WithComponentObject_ReturnTrue(self, complist):
        nonempty_list = adapters.ComponentList(complist)
        comp = complist.getComponent(0)
        assert comp in nonempty_list

    def test__contains__WithComponentObject_ReturnFalse(self, complist,
                                                        maya_component):
        nonempty_list = adapters.ComponentList(complist)
        with maya_component() as comp:
            assert comp not in nonempty_list

    def test__getitem__WithIndex_ReturnComponentObject(self, complist, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        comp = nonempty_list[5]
        indexed = singleindexed(nonempty_list._mlist.getComponent(5))
        assert indexed.isEqual(comp.mobject)

    def test__getitem__WithSliceObjecet_ReturnSlicedComponentList(
            self, complist):
        nonempty_list = adapters.ComponentList(complist)
        newlist = nonempty_list[1:3]
        assert len(newlist) == 2

    def test__setitem__WithMayComponentObject_ReplacingObjectAtIndex(
            self, complist, maya_component, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        with maya_component() as comp:
            indexed = singleindexed(nonempty_list._mlist.getComponent(5))
            nonempty_list[5] = comp
        assert not indexed.isEqual(nonempty_list[5].mobject)

    def test__hash__WithComponentList_ReturnValidHash(self, complist):
        nonempty_list = adapters.ComponentList(complist)
        assert hash(nonempty_list)

    def test__eq__WithComponentList_ReturnTrue(self, complist):
        nonempty_list = adapters.ComponentList(complist)
        nonempty_other = adapters.ComponentList(complist)
        assert nonempty_list == nonempty_other

    def test__ne__WithComponentlist_ReturnTrue(self, complist):
        nonempty_other = adapters.ComponentList(complist)
        complist.remove(0)
        nonempty_list = adapters.ComponentList(complist)
        assert nonempty_list != nonempty_other

    def test__lt__WithComponentList_ReturnTrue(self, complist):
        nonempty_other = adapters.ComponentList(complist)
        complist.remove(0)
        nonempty_list = adapters.ComponentList(complist)
        assert nonempty_list < nonempty_other

    def test__copy__WithComponentList_ReturnCopyOfListObject(self, complist):
        from copy import copy
        nonempty_list = adapters.ComponentList(complist)
        nonempty_other = copy(nonempty_list)
        assert nonempty_list == nonempty_other

    def test__str__WithComponentList_ReturnStringElementWithComponentStrings(
            self, complist):
        nonempty_list = adapters.ComponentList(complist)
        assert str(nonempty_list) == str(complist)

    def test__iter__WithComponentList_ReturnGeneratorContainingComponentObjects(
            self, complist, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        complistit = iter(nonempty_list)
        import types
        assert isinstance(complistit, types.GeneratorType)

    def test__iter__WithIterComponentList_ListOfComponentFactoryMocks(
            self, complist, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        componentlist = list(nonempty_list)
        assert len(componentlist) == complist.length()
        assert all(isinstance(i, ComponentFactoryMock) for i in componentlist)

    def test__reversed__WithComponentList_ReturnReversedGeneratorContainingComponentObjects(
            self, complist, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        reversed_ = itertools.izip(
            xrange(len(nonempty_list) - 1, -1), nonempty_list)
        for i, each in reversed_:
            indexed = singleindexed(each.node)
            assert indexed.isEqual(nonempty_list[i].mobject)

    ## Constructors

    def test__from_strings__WithValidStringComponentList_ReturnValidObjectWithComponents(
            self, complist):
        nonempty_list = adapters.ComponentList.from_strings(
            complist.getSelectionStrings())
        assert nonempty_list

    def test__from_strings__WithListContainingNoComponents_RaiseTypeError(
            self, daglist):
        with pytest.raises(TypeError):
            nonempty_list = adapters.ComponentList.from_strings(
                daglist.getSelectionStrings())

    def test__from_ls__WithListComponentCommand_ReturnValidComponentList(
            self, complist):
        comp = complist.getSelectionStrings(0)[0]
        nonempty_list = adapters.ComponentList.from_ls(comp)
        assert not nonempty_list._mlist.isEmpty()

    def test__from_ls__WithFlattnedList_RaisesOrderedSelectionNotSet(self):
        with pytest.raises(OrderedSelectionsNotSet):
            adapters.ComponentList.from_ls(sl=True, fl=True)

    def test__from_ls__WithFlattnedList_ReturnNonMergedList(
            self, mocker, complist):
        with mocker.patch(
                'mampy.core.listadapters.need_ordered_selection_set',
                return_value=False) as mock:
            comp = complist.getSelectionStrings(0)[0]
            ls = adapters.ComponentList.from_ls(comp, fl=True, merge=False)
            assert len(ls) == len(cmds.ls(comp, fl=True))

    def test__from_selected__WithSelectedComponents_ReturnValidComponentList(
            self, complist):
        cmds.select(complist.getSelectionStrings())
        nonempty_list = adapters.ComponentList.from_selected()
        assert len(cmds.ls(sl=True)) == len(nonempty_list)

    ## Methods

    def test__append__WithMayaComponentObject_AddComponentToLastInList(
            self, complist, maya_component):
        nonempty_list = adapters.ComponentList(complist)
        originlen = len(nonempty_list)
        with maya_component() as comp:
            nonempty_list.append(comp)

        assert comp in nonempty_list
        assert len(nonempty_list) == originlen + 1

    def test__extend__WithComplist_AddComponentsToEndOfList(
            self, complist, maya_component):
        nonempty_list = adapters.ComponentList(complist)
        originlen = len(nonempty_list)

        extendwith = []
        for _ in xrange(5):
            with maya_component() as comp:
                extendwith.append(comp)

        nonempty_list.extend(extendwith)
        assert originlen + 5 == len(nonempty_list)
        assert all(i in nonempty_list for i in extendwith)

    def test__update__WithComponent_UpdateComponentInlist(self, maya_component):
        complist = adapters.ComponentList()
        with maya_component('e') as comp:
            dagname, mobject = comp
            complist.update(comp)
        assert comp in complist

    def test__update__WithComponentList_UpdateComponentInList(
            self, maya_component):
        complist = adapters.ComponentList()
        with maya_component() as comp:
            dagname, mobject = comp

            other_complist = adapters.ComponentList()
            for comptype in ('f', 'vtx', 'map'):
                other_complist.update('{}.{}[*]'.format(str(dagname), comptype))
            complist.update(other_complist)
        assert len(complist) == 1

    def test__pop__WithDefaultValue_ReturnComponentObjectFromGivenIndex(
            self, complist, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        compobject = nonempty_list.pop()
        assert compobject.node not in nonempty_list

    def test__pop__WithIndex_ReturnComponentObjectFromGivenIndex(
            self, complist, mocker):
        mocker.patch.object(
            adapters.ComponentList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=ComponentFactoryMock)

        nonempty_list = adapters.ComponentList(complist)
        compobject = nonempty_list.pop(5)
        assert compobject.node not in nonempty_list

    def test__remove__WithComponentList_RemoveComponentAtGivenIndex(
            self, complist):
        nonempy_list = adapters.ComponentList(complist)
        originlen = len(nonempy_list)
        comp = nonempy_list._getitem_method(0)
        nonempy_list.remove(0)
        assert len(nonempy_list) != originlen
        assert comp not in nonempy_list

    def test__cmdslist__WithComponentList_ReturnListOfStringComponents(
            self, complist):
        nonempty_list = adapters.ComponentList(complist)

        listofstrcomponents = set(nonempty_list.cmdslist())
        expected = set(complist.getSelectionStrings())
        assert listofstrcomponents == expected


class TestMultiComponentList(object):

    def test__init__WithoutParameters_NoErrorsWhileInitObject(self):
        adapters.MultiComponentList()

    def test__update__WithOtherComponentType_ReturnSameLengthMultiComponentListWithDifferentComponents(
            self, maya_component):
        multicomp_list = adapters.MultiComponentList()
        with maya_component() as comp:
            dag, comp = comp
            for tp in ['f', 'e', 'vtx', 'map']:
                strcomp = '{}.{}[*]'.format(str(dag), tp)
                multicomp_list.update(strcomp)
        assert len(multicomp_list) == 1

    def test__getitem__WithMultiComponentList_ReturnComponentListWithAllComponentTypes(
            self, maya_component):
        multicomp_list = adapters.MultiComponentList()
        for _ in xrange(10):
            with maya_component() as comp:
                dag, comp = comp
                for tp in ['f', 'e', 'vtx', 'map']:
                    strcomp = '{}.{}[*]'.format(str(dag), tp)
                    multicomp_list.update(strcomp)

        assert len(multicomp_list[0]) == 4


class DagpathFactoryMock(object):

    def __init__(self, dagpath):
        self.dagpath = dagpath


class TestDagpathList(object):

    def test__init__WithoutParameters_ReturnEmptyDagpathList(self):
        adapters.DagpathList()

    def test__is_valid__WithDependencyNode_ReturnFalse(self, maya_depnode):
        dagpath_list = adapters.DagpathList()
        mlist = om.MSelectionList()
        with maya_depnode() as depnode:
            mlist.add(depnode)
        dagpath_list._mlist = mlist
        assert not dagpath_list.is_valid()

    def test__is_valid__WithComponentList_ReturnTrue(self, complist):
        dagpath_list = adapters.DagpathList()
        dagpath_list._mlist = complist
        assert dagpath_list.is_valid()

    def test__is_valid__WithDagpathList_ReturnTrue(self, daglist):
        dagpath_list = adapters.DagpathList()
        dagpath_list._mlist = daglist
        assert dagpath_list.is_valid

    def test__init__WithoutParameters_ReturnEmptyMListFactory(self):
        dagpath_list = adapters.DagpathList()
        assert not dagpath_list

    def test__init__WithEmptyMSelectionList_ReturnEmptyMListFactory(self):
        dagpath_list = adapters.DagpathList(om.MSelectionList())
        assert not dagpath_list

    def test__contains__WithDagPathObject_ReturnTrue(self, daglist):
        dagpath_list = adapters.DagpathList(daglist)
        dagpath = daglist.getDagPath(5)
        assert dagpath in dagpath_list

    def test__contains__WithDagpathObject_ReturnFalse(self, daglist,
                                                      maya_dagpath):
        dagpath_list = adapters.DagpathList(daglist)
        with maya_dagpath() as dagpath:
            assert dagpath not in dagpath_list

    def test__getitem__WithIndexNumber_ReturnDagpathObject(
            self, daglist, mocker):
        mocker.patch.object(
            adapters.DagpathList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=DagpathFactoryMock)

        dagpath_list = adapters.DagpathList(daglist)
        dagpath = dagpath_list[5]
        assert daglist.getDagPath(5) == dagpath.dagpath

    def test__getitem__WithSliceObjecet_ReturnSlicedDagpathList(
            self, daglist, mocker):
        dagpath_list = adapters.DagpathList(daglist)
        newlist = dagpath_list[1:3]
        assert len(newlist) == 2

    def test__setitem__WithMayaDagPathObject_ReplacingObjectAtIndex(
            self, daglist, maya_dagpath, mocker):
        mocker.patch.object(
            adapters.DagpathList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=DagpathFactoryMock)

        dagpath_list = adapters.DagpathList(daglist)
        with maya_dagpath() as dagpath:
            dagpath_list[5] = dagpath
        assert dagpath_list[5].dagpath == dagpath

    ## Constructors

    def test__from_strings__WithStringDagpathList_ReturnDagpathListContainingDagpaths(
            self, daglist):
        dagpath_list = adapters.DagpathList.from_strings(
            daglist.getSelectionStrings())
        assert dagpath_list

    def test__from_strings__WithStringDependencyList_RaiseTypeError(
            self, deplist):
        with pytest.raises(TypeError):
            dagpath_list = adapters.DagpathList.from_strings(
                deplist.getSelectionStrings())

    def test__from_name__WithDagpathNamePattern_ReturnFullList(self, daglist):
        dagpath_list = adapters.DagpathList.from_name('pCube*')
        # Will include Shape nodes too, so double amount
        assert len(dagpath_list) == 20

    def test__from_selected__WithSelectedDagpaths_ReturnDagpathListWithSelected(
            self, daglist):
        cmds.select(daglist.getSelectionStrings())
        dagpath_list = adapters.DagpathList.from_selected()
        assert len(cmds.ls(sl=True)) == len(dagpath_list)


class DependencyNodeMock(object):

    def __init__(self, dep):
        self.dependency = dep


class TestDependencyNodeList(object):

    def test__init__WithoutParameters_ReturnEmptyDependencyNodeList(self):
        adapters.DependencyNodeList()

    def test__is_valid__WithDependencyNodeList_ReturnTrue(self, deplist):
        depend_list = adapters.DependencyNodeList()
        depend_list._mlist = daglist
        assert depend_list.is_valid

    def test__contains__WithDependencyNodeObject_ReturnTrue(self, deplist):
        depend_list = adapters.DependencyNodeList(deplist)
        depnode = deplist.getDependNode(5)
        assert depnode in depend_list

    def test__contains__WithDependencyNodeObject_ReturnFalse(
            self, deplist, maya_depnode):
        depend_list = adapters.DependencyNodeList(deplist)
        with maya_depnode() as depnode:
            assert depnode not in depend_list

    def test__getitem__WithIndexNumber_ReturnDependencyNodeObject(
            self, deplist, mocker):
        mocker.patch.object(
            adapters.DependencyNodeList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=DependencyNodeMock)

        depend_list = adapters.DependencyNodeList(deplist)
        depnode = depend_list[5]
        assert deplist.getDependNode(5) == depnode.dependency


class PlugMock(object):

    def __init__(self, plug):
        self.plug = plug


class TestPlugList(object):

    def test__init__WithoutParameters_ReturnEmptyPlugList(self):
        adapters.PlugList()

    def test__is_valid__WithPlugList_ReturnTrue(self, pluglist):
        plug_list = adapters.PlugList()
        plug_list._mlist = pluglist
        assert plug_list.is_valid()

    def test__contains__WithPlugObject_ReturnTrue(self, pluglist):
        plug_list = adapters.PlugList(pluglist)
        plug = pluglist.getPlug(5)
        assert plug in plug_list

    def test__contains__WithPlugObject_ReturnFalse(self, pluglist, maya_plug):
        plug_list = adapters.PlugList(pluglist)
        with maya_plug() as plug:
            assert plug not in plug_list

    def test__getitem__WithIndexNumber_ReturnPlugObject(self, pluglist, mocker):
        mocker.patch.object(
            adapters.PlugList,
            '_getitem_type',
            new_callable=mocker.PropertyMock,
            return_value=PlugMock)

        plug_list = adapters.PlugList(pluglist)
        plug = plug_list[5]
        assert pluglist.getPlug(5) == plug.plug
