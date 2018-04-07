# -*- coding: utf-8
"""
Tests for mampy.core.sequence_dep
"""
import contextlib
import copy
import itertools
import types

import mock
import pytest

from maya.api import OpenMaya as om
from mampy.core import sequence_dep


def singleindexed(comp):
    return om.MFnSingleIndexedComponent(comp[1])


@contextlib.contextmanager
def PropertyMock(cls, return_value=None):
    try:
        with mock.patch.object(
                cls,
                '_getitem_type',
                new_callable=mock.PropertyMock,
                return_value=return_value) as mocked:
            yield mocked
    finally:
        pass


class ComponentMock(object):

    def __init__(self, comp):
        self.dagpath, self.mobject = comp

    @property
    def node(self):
        return (self.dagpath, self.mobject)


class TestComponentMListFactory():

    def test_componentfactory_init(self, complist, daglist):
        assert sequence_dep.ComponentMListFactory()
        assert sequence_dep.ComponentMListFactory(complist)

        with pytest.raises(TypeError):
            assert sequence_dep.ComponentMListFactory(daglist)

    def test_componentfactory_from_methods(self, complist, daglist):
        assert sequence_dep.ComponentMListFactory.from_strings(
            complist.getSelectionStrings())
        with pytest.raises(TypeError):
            assert sequence_dep.ComponentMListFactory.from_strings(
                daglist.getSelectionStrings())


class TestComponentMListFactory():

    def test_componentlist_magic_methods(self, complist):
        empty_lst = sequence_dep.ComponentList()
        comp_lst = sequence_dep.ComponentList(complist)
        assert bool(comp_lst) is True
        assert bool(empty_lst) is False
        assert len(comp_lst) == complist.length()
        assert hash(comp_lst)
        assert str(comp_lst) == str(complist)

    def test_componentlist_total_ordering(self, complist):
        empty_lst = sequence_dep.ComponentList()
        comp_lst = sequence_dep.ComponentList(complist)
        copy_lst = copy.copy(comp_lst)

        assert comp_lst > empty_lst
        assert empty_lst < comp_lst
        assert copy_lst <= comp_lst
        assert copy_lst >= comp_lst
        assert copy_lst == comp_lst
        assert comp_lst != empty_lst

    def test_componentlist_contains(self, complist, maya_component):
        comp_lst = sequence_dep.ComponentList(complist)
        contained_component = complist.getComponent(0)
        assert contained_component in comp_lst
        with maya_component() as not_contained_component:
            assert not_contained_component not in comp_lst

    def test_componentlist_getitem_getvalue(self, complist, maya_component):
        with PropertyMock(sequence_dep.ComponentList, ComponentMock) as mocked:
            m_lst = sequence_dep.ComponentList(complist)
            comp = m_lst[0]
            assert mocked.called_with(m_lst._mlist.getComponent(0))

            indexed = singleindexed(m_lst._mlist.getComponent(0))
            assert indexed.isEqual(comp.mobject)

            sliced = m_lst[1:3]
            assert len(sliced) == 2

    @mock.patch('mampy.core.sequence_dep.ComponentList')
    def test_componentlist_getitem_setvalue(self, mock_cl, complist,
                                            maya_component):
        comp_lst = sequence_dep.ComponentList(complist)
        with maya_component() as comp:
            comp_lst._getitem_method = ComponentMock
            comp_lst[5] = comp
            assert comp
            assert comp_lst.__setitem__.called_with(comp)

        # with mock_patch_object(sequence_dep.ComponentList,
        #                        ComponentMock):
        #     comp_lst = sequence_dep.ComponentList(complist)
        #     indexed = singleindexed(comp_lst._mlist.getComponent(5))
        #     with maya_component() as mcomp:
        #         comp_lst[5] = mcomp
        #         assert not indexed.isEqual(comp_lst[5].mobject)
        #

    # def test_componentlist_iter(self, complist):
    #     with mock_patch_object(sequence_dep.ComponentList,
    #                            ComponentMock):
    #         comp_lst = sequence_dep.ComponentList(complist)
    #         iter_ = iter(comp_lst)
    #         assert isinstance(iter_, types.GeneratorType)
    #         assert len(list(iter_)) == 10
    #         assert all(isinstance(_, ComponentMock) for _ in comp_lst)
    #
    # def test_componentlist_reversed(self, complist):
    #     with mock_patch_object(sequence_dep.ComponentList,
    #                            ComponentMock) as mocked:
    #         mocked_lst = sequence_dep.ComponentList(complist)
    #         reversed_ = itertools.izip(
    #             xrange(len(mocked_lst) -1 , -1), mocked_lst)
    #         for i, each in reversed_:
    #             indexed = singleindexed(each.node)
    #             assert indexed.isEqual(nonempty_list[i].mobject)
    #
