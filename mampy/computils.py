# -*- coding: utf-8 -*-
"""
Utility functions used to create or collect dag components.
"""
import collections

from maya import cmds
import maya.api.OpenMaya as api

from mampy.selections import SelectionList
from mampy.components import MeshVert


__all__ = ['get_border_loop_from_edge_index', 'get_border_loop_from_edge',
           'get_indices_sharing_edge_border', 'get_border_edges_from_selection',
           'get_outer_edges_in_loop', 'get_connected_components']


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

        outer_edges.append(tuple(
            MeshVert.create(str(connected.dagpath)).add(i)
            for i in [outer_vert, inner_vert]
        ))
    dag = str(connected.dagpath)
    return outer_edges, MeshVert.create(dag).add(indices)


def get_connected_components(component, convert_to_origin_type=True):
    """
    Loop through given indices and check if they are connected. Maps
    connected indices and returns a dict.

    .. todo: rewrite if / elif segments to something a bit more pleasing to
            the eyes
    """
    def is_ids_in_loop(ids):
        """
        Check if id is connected to any indices currently in
        connected[connected_set_count] key.
        """
        id1, id2 = ids
        for edge in connected[connected_set_count]:
            if id1 in edge or id2 in edge:
                return True
        return False

    def get_return_list():
        """
        Create return list containing connected components.
        """
        # Create list and append connected comps as list object.
        return_list = SelectionList()
        for i in connected.itervalues():
            return_comp = MeshVert.create(component.dagpath)
            return_comp.add(set(sum(i, ())))
            if component.type in [api.MFn.kMeshEdgeComponent,
                                  api.MFn.kMeshPolygonComponent]:
                converted = return_comp.convert_to(component.type, internal=True)
            else:
                converted = return_comp.convert_to(component.type)
            return_list.append(converted)
        return return_list

    # Needs to make sure that edges does not extend outside of the
    # selection border.
    if component.type == api.MFn.kMeshEdgeComponent:
        edge = component
    elif component.type in [api.MFn.kMeshVertComponent,
                            api.MFn.kMeshMapComponent]:
        edge = component.to_edge(internal=True)
    else:
        edge = component.to_edge()

    # Set up necessary variables
    connected_set_count = 0
    connected = collections.defaultdict(set)
    indices = set([edge.mesh.getEdgeVertices(e) for e in edge.indices])
    while indices:

        connected_set_count += 1
        connected[connected_set_count].add(indices.pop())

        # Map connected until no match can be found
        while True:
            loop_growing = False
            for ids in indices.copy():
                if is_ids_in_loop(ids):
                    loop_growing = True
                    connected[connected_set_count].add(ids)
                    indices.remove(ids)
            if not loop_growing:
                break

    return get_return_list()
