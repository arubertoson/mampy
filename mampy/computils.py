# -*- coding: utf-8 -*-
"""
Utility functions used to create or collect dag components.
"""
import logging
import collections

from maya import cmds

import mampy
from mampy.dgcontainers import SelectionList
from mampy.dgcomps import MeshVert, MeshMap


__all__ = ['get_border_loop_from_edge_index', 'get_border_loop_from_edge',
           'get_indices_sharing_edge_border', 'get_border_edges_from_selection',
           'get_outer_edges_in_loop']


logger = logging.getLogger(__file__)
# logger.setLevel(logging.DEBUG)


def get_border_loop_from_edge_index(index):
    return set(sorted([int(i) for i in cmds.polySelect(q=True, edgeBorder=index)]))


def get_border_loop_from_edge(component):
    return set([
        tuple(border for border in get_border_loop_from_edge_index(idx))
        for idx in component.indices
    ])


def get_indices_sharing_edge_border(component):
    """Get indices sharing border edge loop from component."""
    edge_borders = SelectionList()
    for border in get_border_loop_from_edge(component):
        new_component = component.new()
        for index in component.indices:
            if index in border:
                new_component.add(index)
        edge_borders.append(new_component)
    return edge_borders


def get_border_edges_from_selection(edge_selection):
    """Get border edges from selection and return a new selection list."""
    border_edges = SelectionList()
    for component in edge_selection.itercomps():
        borders = component.new()
        for index in component.indices:
            if not component.is_border(index):
                continue
            borders.add(index)
        if borders:
            border_edges.append(borders)
    return border_edges


def get_outer_edges_in_loop(connected):
    """
    Return outer edges from a component object containing connected
    edges.
    """
    # Get tuples with vert ids representing edges
    edges = [connected.mesh.getEdgeVertices(i) for i in connected.indices]
    indices = set(sum(edges, ()))

    # Create a counter and count vert ids
    vert_count = collections.Counter()
    vert_count.update(i for e in edges for i in e)

    # Edges are represented as a tuple containing MeshVerts. This is
    # so in case of vector creation you will get the right direction.
    outer_edges = SelectionList()
    for each in vert_count.most_common()[-2:]:

        outer_vert = each[0]
        outer_edge = [e for e in edges if outer_vert in e].pop()
        inner_vert = [v for v in outer_edge if not outer_vert == v].pop()
        indices.remove(outer_vert)

        vert = MeshVert.create(str(connected.dagpath))
        vert.add([outer_vert, inner_vert])
        outer_edges.append(vert)

    dag = str(connected.dagpath)
    return outer_edges, MeshVert.create(dag).add(indices)


def get_vert_order_on_edge_row(indices):
    """
    .. note:: Should probably be moved to mampy.
    """
    idx = 0
    next_ = None
    sorted_ = []
    while indices:

        edge = indices.pop(idx)
        if next_ is None:
            next_ = edge[-1]

        sorted_.append(next_)
        for i in indices:
            if next_ in i:
                idx = indices.index(i)
                next_ = i[-1] if next_ == i[0] else i[0]
                break

    return sorted_


def get_shells(components=None):
    """
    Collect selected uv shells.
    """
    s = components or mampy.selected()
    if not s:
        h = mampy.ls(hl=True)
        if not h:
            return logger.warn('Nothing selected.')
        s.extend(h)

    shells = SelectionList()
    for c in s.itercomps():
        if not c:
            c = MeshMap(c.dagpath).get_complete()
        else:
            c = c.to_map()

        count, array = c.mesh.getUvShellsIds()
        if c.is_complete():
            wanted = set(xrange(count))
        else:
            wanted = set([array[idx] for idx in c.indices])

        for each in wanted:
            shell = MeshMap.create(c.dagpath)
            shell.add([idx for idx, num in enumerate(array) if num == each])
            shells.append(shell)
    return list(shells.itercomps())


if __name__ == '__main__':
    pass
