"""
Tests for mampy.helpers.computils
"""
import itertools
from contextlib import contextmanager

import pytest

from maya import cmds
from maya.api import OpenMaya as om

from mampy.core.components2 import (MeshEdge, MeshMap, MeshPolygon, MeshVertex,
                                    SingleIndexComponent)
from mampy.helpers import computils as cu

compclasses = SingleIndexComponent.__subclasses__()


@pytest.mark.parametrize("comptype", compclasses)
def test_init_convert_is_valid_object(comptype, maya_dagpath):
    with maya_dagpath() as dpath:
        compobj = comptype.from_complete(dpath)
        assert cu.convert(compobj)


@pytest.mark.parametrize("comptype", compclasses)
def test_to_face_convert_return_MeshPolygon_object(comptype, maya_dagpath):
    with maya_dagpath() as dpath:
        compobj = comptype.from_complete(dpath)
        face = cu.convert(compobj).to_face()
        assert isinstance(face, MeshPolygon) and face.is_complete()


@pytest.mark.parametrize("comptype", compclasses)
def test_to_edge_convert_return_MeshEdge_object(comptype, maya_dagpath):
    with maya_dagpath() as dpath:
        compobj = comptype.from_complete(dpath)
        edge = cu.convert(compobj).to_edge()
        assert isinstance(edge, MeshEdge) and edge.is_complete()


@pytest.mark.parametrize("comptype", compclasses)
def test_to_vert_convert_return_MeshVert_object(comptype, maya_dagpath):
    with maya_dagpath() as dpath:
        compobj = comptype.from_complete(dpath)
        vert = cu.convert(compobj).to_vert()
        assert isinstance(vert, MeshVertex) and vert.is_complete()


@pytest.mark.parametrize("comptype", compclasses)
def test_to_map_convert_return_MeshMap_object(comptype, maya_dagpath):
    with maya_dagpath() as dpath:
        compobj = comptype.from_complete(dpath)
        map = cu.convert(compobj).to_map()
        assert isinstance(map, MeshMap) and map.is_complete()


@pytest.mark.parametrize("comptype", compclasses)
def test_init_connected_return_nonzero_object(comptype, nonsolid):
    with nonsolid() as dpath:
        compobj = comptype.from_dagpath(dpath)
        compobj.add(xrange(6, 11))
        assert cu.connected


@contextmanager
def polyplane(w=10, h=10):
    try:
        plane, _ = cmds.polyPlane(sx=w, sy=h)
        yield plane
    finally:
        cmds.delete(plane)


def test_get_connected_connected_return_correct_len():
    with polyplane(10, 10) as dpath:
        compobj = MeshPolygon.from_dagpath(dpath)
        indices = [
            set([23, 32, 33, 42, 43, 52, 53, 62, 63, 73]),
            set([66, 67, 76, 77]),
            set([26, 27, 36, 37]),
            set([14]),
            set([84])
        ]
        compobj.add(i for i in itertools.chain(*indices))
        cn = cu.connected(compobj)
        assert len(list(cn)) == 5


def test_get_connected_connected_return_correct_indices():
    with polyplane(10, 10) as dpath:
        compobj = MeshPolygon.from_dagpath(dpath)
        indices = set([
            frozenset([23, 32, 33, 42, 43, 52, 53, 62, 63, 73]),
            frozenset([66, 67, 76, 77]),
            frozenset([26, 27, 36, 37]),
            frozenset([84]),
            frozenset([14])
        ])
        compobj.add(i for i in itertools.chain(*indices))
        cn = cu.connected(compobj)
        assert indices == set(frozenset(i.indices) for i in cn)


def test_string_to_dagpath_return_MDagPath_object(xcubes):
    with xcubes(1) as cubes:
        for cube in cubes:
            assert isinstance(cu.string_to_dagpath(cube), om.MDagPath)


@pytest.mark.parametrize("comptype", compclasses)
def test_min_max_mampy_component_object_return_max_and_min_MPoint(
        comptype, maya_dagpath):
    with maya_dagpath() as dpath:
        compobj = comptype.from_complete(dpath)
        if compobj.type == om.MFn.kMeshMapComponent:
            for each in compobj.points():
                print(each)
        # min_, max_ = cu.min_max():
        # assert min_ in [om.MPoint(-.5, -.5, -.5), om.MPoint(0, 0, 0)]
        # print cu.min_max(compobj)
