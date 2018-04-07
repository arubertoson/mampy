"""
tests for mampy/core/dagnodes.py -> DependencyNode
"""
import contextlib

from maya import cmds

import mampy
from mampy.core import utils


@contextlib.contextmanager
def mesh_cube(name):
    try:
        cube = cmds.polyCube(n=name)
        yield cube
    finally:
        cmds.delete(cube)


def test_daglist_empty_with_dependency_node_selected():
    with mesh_cube('test_cube') as cube:
        mesh, plug = cube
        cmds.select(plug)
        assert not mampy.daglist()
