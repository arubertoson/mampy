"""
Tests for mampy.core.meshlookup module
"""
from maya.api import OpenMaya as om

from mampy.core import meshlookup as ml


def test__missing__meshlookup_creating_new_key(maya_dagpath):
    with maya_dagpath() as dpath:
        mesh = om.MFnMesh(dpath)
        assert isinstance(ml.meshlookup.instance()[mesh], ml.MeshLookupTable)


def add(l1, l2):
    return l1 + l2

def union(s1, s2):
    return s1.update(s2)

def test_MeshLookupTable(maya_dagpath, benchmark):
    with maya_dagpath() as dpath:
        mesh = om.MFnMesh(dpath)
        # mesh_lookup = ml.meshlookup.instance()[mesh]
        # benchmark(mesh_lookup._edge_lookupmaps)
        # benchmark(mesh_lookup._lookupmaps)
        li1 = list(xrange(10000))
        li2 = list(xrange(10000))
        benchmark(add, li1, li2)
        # benchmark(union, set(li1), set(li2))
