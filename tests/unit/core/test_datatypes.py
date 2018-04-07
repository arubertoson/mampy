"""
"""
from mampy.core.components2 import (MeshEdge, MeshVertex, MeshPolygon, MeshMap)
from mampy.core.datatypes import IndexValueMap

from maya.api.OpenMaya import MPoint

index_point_map = {
    0L: MPoint(1, 2, 3),
    1L: MPoint(10, 2, 5),
    2L: MPoint(5, 8, 2),
    3L: MPoint(1, 5, 4),
    4L: MPoint(5, 8, 2),
    5L: MPoint(1, 5, 4)
}

index_point_map_nested = {
    0L:
    IndexValueMap(
        {
            0: MPoint(1, 2, 3),
            1: MPoint(10, 2, 5),
            2: MPoint(5, 8, 2),
            3: MPoint(1, 5, 4)
        }
    ),
    1L:
    IndexValueMap(
        {
            2: MPoint(1, 2, 3),
            3: MPoint(10, 2, 5),
            4: MPoint(5, 8, 2),
            5: MPoint(1, 5, 4)
        }
    )
}


def test_has_point_IndexValueMap_if_point_is_in_dict_object():
    assert IndexValueMap(index_point_map).has_point(index_point_map[0])


def test_has_point_IndexValueMap_if_face_or_edge_list():
    assert IndexValueMap(index_point_map_nested).has_point(index_point_map[0])


def test_iter_IndexValueMap_empty_iter():
    assert not list(IndexValueMap())


def test_iterpoints_IndexValueMap_returning_list_of_MPoints():
    idxptmap = IndexValueMap(index_point_map)
    assert all([isinstance(pt, MPoint) for pt in idxptmap._iterpoints()])


def test_iternestedpoints_IndexValueMap_returning_list_of_MPoints():
    idxptmap = IndexValueMap(index_point_map_nested)
    assert all([isinstance(pt, MPoint) for pt in idxptmap._iternestedpoints()])


def test_iter_IndexValueMap_iter_dispatcher():
    idxptmap = IndexValueMap(index_point_map)
    idxptmap_nested = IndexValueMap(index_point_map_nested)
    assert all([point in list(idxptmap_nested) for point in idxptmap])
