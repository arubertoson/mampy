"""
tests for mampy/core/dagnodes.py -> DependencyNode
"""
import contextlib

from maya import cmds

import mampy


@contextlib.contextmanager
def mesh_cube(name):
    try:
        cube = cmds.polyCube()
        yield cube
    finally:
        cmds.delete(cube)


def test_daglist_empty_with_dependency_node_selected():
    with mesh_cube('test_cube') as cube:
        mesh, plug = cube
        cmds.select(plug)
        assert not mampy.daglist()

# def test_module_setup():
#     assert DependencyNode()
#         with pytest.raises(TypeError) as mampy.daglist()
#         assert DependencyNode(plug)
