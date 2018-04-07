"""
Tests for mampy.core.compnormals module
"""
from maya.api import OpenMaya as om

from mampy.core import compnormals as cnorm


class CompMock(object):
    pass


class NormalsMock(cnorm.ComponentNormalsBase):

    @property
    def normals(self):
        return list(xrange(10))


def test_output_normal_space():
    assert cnorm.output_normal_space(om.MSpace.kWorld) == 'World'
    assert cnorm.output_normal_space(om.MSpace.kObject) == 'Object'


def test_weighted_Weighted_return_value():
    weighted = cnorm.Weighted()
    assert weighted.weighted is False


def test_weighted_Weighted_change_value():
    weighted = cnorm.Weighted()
    weighted.weighted = True
    assert weighted.weighted is True


def test_normals_ComponentNormalsBase_property():
    cnbase = NormalsMock(CompMock())
    assert cnbase.normals
    assert cnbase.normals[1] == 1
    assert list(cnbase) == cnbase.normals


def test_space_ComponentNormalsBase_property():
    cnbase = NormalsMock(CompMock())
    assert cnbase.space == cnbase._mfn_default_space
    cnbase.space = 124
    assert cnbase.space == 124


## Integration
