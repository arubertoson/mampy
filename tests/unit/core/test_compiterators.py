"""
Tests for mampy.core.compiterators module
"""
from contextlib import contextmanager
import pytest
from mampy.core import compiterators as cit

from maya.api import OpenMaya as om
from maya import cmds


@pytest.fixture(scope='module')
def nonsolid_component():
    cube, node = cmds.polyCube(n='test_nonsolid')
    cmds.setAttr(node + ".subdivisionsHeight", 2)
    cmds.setAttr(node + ".subdivisionsDepth", 2)
    cmds.delete(cube + '.f[3:4]')

    yield om.MSelectionList().add(cube).getComponent(0)
    cmds.delete(cube)


@pytest.fixture(scope='module')
def meshmapit(nonsolid_component):
    return cit.MeshMapIterator(*nonsolid_component)


def test_index_MeshVertexIterator_return_index_without_runtimeerror(
        maya_component):
    with maya_component(type='vtx') as comp:
        it = cit.MeshVertexIterator(*comp)

        assert it.index() == 0
        it.setIndex(5)
        assert it.index() == 5


def test_next_MeshPolygonIterator_using_next_without_raising_runtimeerror(
        maya_component):
    with maya_component(type='f') as comp:
        it = cit.MeshPolygonIterator(*comp)
        it.next()
        assert it


class MeshMap(object):

    def __init__(self, dpath, comp):
        self.dagpath = dpath
        self.comp = comp

    @property
    def indices(self):
        return set(xrange(10))

    @property
    def mesh(self):
        return om.MFnMesh(self.dagpath)

    @property
    def node(self):
        return (self.dagpath, self.comp)


def test__init__MeshMapIterator_return_complete_iterator(meshmapit):
    # with maya_component(type='map') as comp:
    #     it = cit.MeshMapIterator(*comp)

    indexed = om.MFnSingleIndexedComponent(meshmapit.mobject)
    assert len(meshmapit) == indexed.elementCount


# def test_init_MeshMapIterator_partial_iterator(maya_dagpath):
#     with maya_dagpath() as dpath:
#         indexed = om.MFnSingleIndexedComponent()
#         comp = indexed.create(om.MFn.kMeshMapComponent)
#         indexed.addElements(list(xrange(2, 5)))

#         it = cit.MeshMapIterator(dpath, comp)
#         for idx, cmp in enumerate(it):
#             assert cmp.index() == 2, 'Expected Correct Index'

# def test_position_MeshMapIterator_returing_correct_point_value(maya_component):
#     with maya_component(type='map') as dpath:
#         pass
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

## Integration
