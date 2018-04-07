"""
"""
import random

import pytest

from maya import cmds
from maya.api import OpenMaya as om

from mampy.definitions import ROOT_DIR
from mampy.core import meshlookup

# def test_meshlookup_(maya_dagpath, benchmark):
#     with maya_dagpath() as dagpath:
#         polycube = cmds.ls('polyCube*').pop(0)
#         cmds.setAttr(polycube + ".subdivisionsWidth", 50)
#         cmds.setAttr(polycube + ".subdivisionsDepth", 50)
#         cmds.setAttr(polycube + ".subdivisionsHeight", 50)
#         benchmark(meshlookup.createmeshtable, dagpath)

# def test_meshlookup(maya_dagpath, benchmark):
#     with maya_dagpath() as dagpath:
#         polycube = cmds.ls('polyCube*').pop(0)
#         cmds.setAttr(polycube + ".subdivisionsWidth", 50)
#         cmds.setAttr(polycube + ".subdivisionsDepth", 50)
#         cmds.setAttr(polycube + ".subdivisionsHeight", 50)
#         mesh = om.MFnMesh(dagpath)
#         benchmark(meshlookup.MeshLookupTable, mesh)

import collections


def getshells(ids):
    shells = collections.defaultdict(list)
    index = 0
    for shell in ids:
        shells[shell].append(index)
        index += 1
    return shells


def test_shells(maya_dagpath, benchmark):
    with maya_dagpath() as dagpath:
        polycube = cmds.ls('polyCube*').pop(0)
        cmds.setAttr(polycube + ".subdivisionsWidth", 100)
        cmds.setAttr(polycube + ".subdivisionsDepth", 100)
        cmds.setAttr(polycube + ".subdivisionsHeight", 100)
        mesh = om.MFnMesh(dagpath)
        c, l = mesh.getUvShellsIds()
        benchmark(getshells, l)


from mampy import _mutils


def test_mutils(maya_dagpath, benchmark):
    with maya_dagpath() as dagpath:
        polycube = cmds.ls('polyCube*').pop(0)
        cmds.setAttr(polycube + ".subdivisionsWidth", 100)
        cmds.setAttr(polycube + ".subdivisionsDepth", 100)
        cmds.setAttr(polycube + ".subdivisionsHeight", 100)
        mesh = om.MFnMesh(dagpath)
        c, l = mesh.getUvShellsIds()
        res = benchmark(_mutils.getshells, l)


def test_mutilStr(maya_dagpath, benchmark):
    with maya_dagpath() as dagpath:
        polycube = cmds.ls('polyCube*').pop(0)
        cmds.setAttr(polycube + ".subdivisionsWidth", 100)
        cmds.setAttr(polycube + ".subdivisionsDepth", 100)
        cmds.setAttr(polycube + ".subdivisionsHeight", 100)
        # mesh = om.MFnMesh(dagpath)
        # c, l = mesh.getUvShellsIds()
        res = benchmark(_mutils.getshells, str(dagpath))

# def test_something():
#     from ctypes import cdll
#     mydll = cdll.LoadLibrary(ROOT_DIR + '/lib/math.dll')
#     assert mydll.sum(5, 5) == 10

# from mampy.core.components2 import (
#     COMPONENT_STRING_TYPES, AbstractComponentNormals, MeshVertNormal,
#     MeshPolygonNormal, MeshEdgeNormal, MeshEdge, MeshMap, MeshMapIterator,
#     MeshPolygon, MeshVertex, SingleIndexComponent
# )
# from mampy.core.datatypes import BoundingBox2D

# normalclasses = AbstractComponentNormals.__subclasses__()

# @pytest.mark.parametrize("normtype", normalclasses)
# def test_init_AbstractComponentNormals_return_nonzero_objec(
#     normtype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         # Doesn't really matter what component object we use to perform
#         # the tests
#         compobj = MeshVertex.from_complete(dpath)
#         assert normtype(compobj, om.MSpace.kWorld)

# @pytest.mark.parametrize("normtype", normalclasses)
# def test_iter_AbstractComponentNormals_return_valid_vector(
#     normtype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = MeshVertex.from_complete(dpath)
#         normobj = normtype(compobj, om.MSpace.kWorld)
#         normal = iter(normobj).next()
#         assert isinstance(normal, (om.MFloatVector, om.MVector))

# @pytest.mark.parametrize("normtype", normalclasses)
# def test_getitem_AbstractComponentNormals_return_valid_vector(
#     normtype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = MeshVertex.from_complete(dpath)
#         normal = normtype(compobj, om.MSpace.kWorld)[0]
#         assert isinstance(normal, (om.MFloatVector, om.MVector))

# def test_getitem_MeshVertNormal_return_valid_vector_value(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshVertex.from_complete(dpath)
#         normal = MeshVertNormal(compobj, om.MSpace.kWorld)
#         control_normal = compobj.mesh.getVertexNormals(
#             normal.weighted, normal.space
#         )
#         assert normal[0] == control_normal[0]

# def test_getitem_MeshPolygonNormal_return_valid_vector_value(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshPolygon.from_complete(dpath)
#         normal = MeshPolygonNormal(compobj, om.MSpace.kWorld)
#         control_normal = compobj.mesh.getPolygonNormal(0, normal.space)
#         assert normal[0] == control_normal

# def test_getitem_MeshEdgeNormal_return_valid_vector_value(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshEdge.from_complete(dpath)
#         normal = MeshEdgeNormal(compobj, om.MSpace.kWorld)

#         pair = compobj.mesh.getEdgeVertices(0)
#         normals = compobj.mesh.getVertexNormals(normal.weighted, normal.space)
#         v1, v2 = normals[pair[0]], normals[pair[1]]
#         control_normal = (v1 + v2) / 2

#         assert normal[0] == control_normal

# def test_vertpairs_MeshEdgeNormal_return_valid_vector_value(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshEdge.from_complete(dpath)
#         normal = MeshEdgeNormal(compobj, om.MSpace.kWorld)

#         pair = compobj.mesh.getEdgeVertices(0)
#         normals = compobj.mesh.getVertexNormals(normal.weighted, normal.space)
#         v1, v2 = normals[pair[0]], normals[pair[1]]

#         assert normal.vertpairs[frozenset(pair)] == (v1, v2)

# compclasses = SingleIndexComponent.__subclasses__()

# def test_init_SingleIndexComponent_class_with_maya_component(maya_component):
#     with maya_component() as comp:
#         assert SingleIndexComponent(*comp)

# def test_init_SingleIndexComponent_class_with_maya_null_component(maya_dagpath):
#     mlist = om.MSelectionList()
#     with maya_dagpath() as dpath:
#         mlist.add(dpath)
#         comp = mlist.getComponent(0)
#         assert not (SingleIndexComponent(*comp))

# def test_eq_SingleIndexComponent(maya_component):
#     with maya_component() as comp:
#         comp1 = SingleIndexComponent(*comp)
#         comp2 = SingleIndexComponent(*comp)
#         assert comp1 == comp2

# def test_ne_SingleIndexComponent(maya_component):
#     with maya_component() as comp:
#         with maya_component() as other_comp:
#             comp1 = SingleIndexComponent(*comp)
#             comp2 = SingleIndexComponent(*other_comp)
#             assert comp1 != comp2

# def test_mesh_SingleIndexComponent_returning_valid_object(maya_component):
#     with maya_component() as comp:
#         comp = SingleIndexComponent(*comp)
#         assert isinstance(comp.mesh, om.MFnMesh)

# # TODO: Test dagnode

# def test_node_SingleIndexComponent_returning_maya_component(maya_component):
#     with maya_component() as comp:
#         comp = SingleIndexComponent(*comp)
#         assert SingleIndexComponent(*comp.node)

# def test_type_SingleindexComponent_returning_maya_mfntype(maya_component):
#     with maya_component() as comp:
#         type_ = comp[1].apiType()
#         comp = SingleIndexComponent(*comp)
#         assert comp.type == type_

# def test_strtype_SingleIndexComponent_returning_maya_stringtype(maya_component):
#     with maya_component() as comp:
#         comp = SingleIndexComponent(*comp)
#         assert comp.strtype == COMPONENT_STRING_TYPES[comp.type]

# def test_hash_SingleIndexComponent_is_valid_hash(maya_component):
#     with maya_component() as comp:
#         comp = SingleIndexComponent(*comp)
#         assert {comp: "Test"}

# comptypes = [
#     om.MFn.kMeshPolygonComponent, om.MFn.kMeshVertComponent,
#     om.MFn.kMeshEdgeComponent, om.MFn.kMeshMapComponent
# ]

# @pytest.mark.parametrize("comptype", comptypes)
# def test_factory_SingleIndexComponent_returning_valid_component_object(
#     maya_dagpath, comptype
# ):
#     indexed = om.MFnSingleIndexedComponent()
#     comp = indexed.create(comptype)
#     with maya_dagpath() as dpath:
#         assert not (SingleIndexComponent.factory(comptype, dpath, comp))

# indices_count = {
#     om.MFn.kMeshPolygonComponent: 'numPolygons',
#     om.MFn.kMeshEdgeComponent: 'numEdges',
#     om.MFn.kMeshVertComponent: 'numVertices',
#     om.MFn.kMeshMapComponent: 'numUVs',
# }

# def get_component_count(dagpath, comptype):
#     mesh = om.MFnMesh(dagpath)
#     nums = getattr(mesh, indices_count[comptype])
#     return nums() if callable(nums) else nums

# @pytest.mark.parametrize("comptype", compclasses)
# def test_len_SingleIndexComponent_returning_right_component_count(
#     comptype, maya_component
# ):
#     with maya_component() as comp:
#         compobj = comptype(*comp)
#         count = get_component_count(comp[0], compobj.type)
#         assert len(compobj) == count

# @pytest.mark.parametrize("comptype", compclasses)
# def test_contains_SingleIndexComponent_containing_index(
#     comptype, maya_component
# ):
#     with maya_component() as comp:
#         compobj = comptype(*comp)
#         count = get_component_count(comp[0], compobj.type)
#         assert random.randint(0, count - 1) in compobj

# @pytest.mark.parametrize("comptype", compclasses)
# def test_from_dagpath_SingleIndexComponent_creating_empty_component(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_dagpath(dpath)
#         assert not (compobj)

# @pytest.mark.parametrize("comptype", compclasses)
# def test_add_SingleIndexComponent_add_elements_to_component(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_dagpath(dpath)
#         compobj.add(0)
#         assert compobj

# @pytest.mark.parametrize("comptype", compclasses)
# def test_from_complete_SingleIndexComponent_creating_complete_component(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_complete(dpath)
#         compcount = get_component_count(dpath, compobj.type)
#         assert compcount == len(compobj)

# @pytest.mark.parametrize("comptype", compclasses)
# def test_is_complete_SingleIndexComponent_verifying_complete_component(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_complete(dpath)
#         assert compobj.is_complete()

# @pytest.mark.parametrize("comptype", compclasses)
# def test_is_complete_SingleIndexComponent_verifying_incomplete_component(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_dagpath(dpath)
#         assert not (compobj.is_complete())

# @pytest.mark.parametrize("comptype", compclasses)
# def test_points_SingleIndexComponent_list_of_points(comptype, maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_dagpath(dpath)
#         assert all([isinstance(pt, om.MPoint) for pt in compobj.points()])

# @pytest.mark.parametrize("comptype", compclasses)
# def test_points_SingleIndexComponent_list_of_points(comptype, maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_dagpath(dpath)
#         for index in compobj.indices:
#             if compobj.type == om.MFn.kMeshVertComponent:
#                 assert comptype.points()[index] == compobj.mesh.getPoint(index)

# def test_init_MeshMapIterator_return_complete_iterator(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshMap.from_complete(dpath)
#         iterator = iter(MeshMapIterator(compobj)).next()
#         assert iterator.count() == len(compobj)

# def test_init_MeshMapIterator_partial_iterator(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshMap.from_dagpath(dpath)
#         compobj.add(list(xrange(2, 5)))
#         for idx, cmp in enumerate(compobj):
#             assert cmp.index() == 2 + idx

# def test_position_MeshMapIterator_returing_correct_point_value(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshMap.from_complete(dpath)
#         iterator = MeshMapIterator(compobj)
#         for uvmap in iterator:
#             assert uvmap.position() == compobj.points()[uvmap.index()]

# def test_getVertex_MeshMapIterator_returning_vert_at_uv_index(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshMap.from_complete(dpath)
#         iterator = iter(MeshMapIterator(compobj)).next()
#         assert iterator.getVertex() == 0

# def test_getConnectedUVs_MeshMapIterator_returning_connected_uvids(nonsolid):
#     with nonsolid() as dpath:
#         meshmap = MeshMap.from_complete(dpath)
#         for uv in meshmap:
#             if uv.index() == 0:
#                 assert uv.getConnectedUVs() == set([23, 2, 1])
#             elif uv.index() == 4:
#                 assert uv.getConnectedUVs() == set([27, 2, 5, 6])
#             elif uv.index() == 22:
#                 assert uv.getConnectedUVs() == set([24, 23])
#             elif uv.index() == 25:
#                 assert uv.getConnectedUVs() == set([24, 27, 2, 23])

# def test_getConnectedVertices_MeshMapIterator_returning_connected_vertids(
#     nonsolid
# ):
#     with nonsolid() as dpath:
#         meshmap = MeshMap.from_complete(dpath)
#         for uv in meshmap:
#             if uv.index() == 0:
#                 assert uv.getConnectedVertices() == set([14, 2, 1])
#             if uv.index() == 4:
#                 assert uv.getConnectedVertices() == set([6, 2, 5])
#             if uv.index() == 22:
#                 assert uv.getConnectedVertices() == set([10, 14])
#             if uv.index() == 25:
#                 assert uv.getConnectedVertices() == set([10, 6, 2, 14])

# def test_getConnectedFaces_MeshMapIterator_returning_connected_faceids(
#     nonsolid
# ):
#     with nonsolid() as dpath:
#         meshmap = MeshMap.from_complete(dpath)
#         for uv in meshmap:
#             if uv.index() == 0:
#                 assert uv.getConnectedFaces() == set([11, 0])
#             if uv.index() == 4:
#                 assert uv.getConnectedFaces() == set([13, 2, 1])
#             if uv.index() == 22:
#                 assert uv.getConnectedFaces() == set([10])
#             if uv.index() == 25:
#                 assert uv.getConnectedFaces() == set([10, 11, 12, 13])

# def test_getConnectedEdges_MeshMapIterator_returning_connected_edgeids(
#     nonsolid
# ):
#     with nonsolid() as dpath:
#         meshmap = MeshMap.from_complete(dpath)
#         for uv in meshmap:
#             if uv.index() == 0:
#                 assert uv.getConnectedEdges() == set([0, 7, 21])
#             if uv.index() == 4:
#                 assert uv.getConnectedEdges() == set([11, 2, 9])
#             if uv.index() == 22:
#                 assert uv.getConnectedEdges() == set([17, 19])
#             if uv.index() == 25:
#                 assert uv.getConnectedEdges() == set([27, 28, 29, 30])

# def test_onBoundary_MeshMapIterator_returning_true_when_uvid_on_boundary(
#     nonsolid
# ):
#     with nonsolid() as dpath:
#         meshmap = MeshMap.from_complete(dpath)
#         for uv in meshmap:
#             if uv.index() == 0:
#                 assert uv.onBoundary()
#             if uv.index() == 4:
#                 assert uv.onBoundary()
#             if uv.index() == 22:
#                 assert uv.onBoundary()
#             if uv.index() == 25:
#                 assert not uv.onBoundary()

# @pytest.mark.parametrize("comptype", compclasses)
# def test_bbox_SingleIndexComponent_returning_BoundingBox_object(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = MeshPolygon.from_complete(dpath)
#         assert isinstance(compobj.bbox(), (om.MBoundingBox, BoundingBox2D))

# @pytest.mark.parametrize("comptype", compclasses)
# def test_getitem_SingleIndexComponent_returning_iter_with_index(
#     comptype, maya_dagpath
# ):
#     with maya_dagpath() as dpath:
#         compobj = comptype.from_complete(dpath)
#         assert compobj[5].index() == 5

# def test_is_face_MeshPolygon_return_true(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshPolygon.from_complete(dpath)
#         assert compobj.is_face()
#         assert not compobj.is_vert()
#         assert not compobj.is_edge()
#         assert not compobj.is_map()

# def test_is_edge_MeshEdge_return_true(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshEdge.from_complete(dpath)
#         assert compobj.is_edge()
#         assert not compobj.is_face()
#         assert not compobj.is_vert()
#         assert not compobj.is_map()

# def test_is_vert_MeshVertex_return_true(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshVertex.from_complete(dpath)
#         assert compobj.is_vert()
#         assert not compobj.is_edge()
#         assert not compobj.is_face()
#         assert not compobj.is_map()

# def test_is_map_MeshMap_return_true(maya_dagpath):
#     with maya_dagpath() as dpath:
#         compobj = MeshMap.from_complete(dpath)
#         assert compobj.is_map()
#         assert not compobj.is_vert()
#         assert not compobj.is_edge()
#         assert not compobj.is_face()
