"""
This module implements the Mampy API.

:copyright: (c) 2016 by Marcus Albertsson
:license: MIT, see LICENSE for more details.
"""
from __future__ import absolute_import, unicode_literals

from .core.components import SingleIndexComponent, MeshPolygon, MeshEdge, MeshMap, MeshVert
from .core.selectionlist import ComponentList, DagpathList, DependencyList, PlugList


def _get_dagpath_list_from_type(list_object, *args, **kwargs):
    if not args and not kwargs:
        return list_object.from_selection()
    if args and isinstance(args[0], basestring):
        return list_object.from_name(args[0])
    return list_object.from_ls(*args, **kwargs)


def compls(*args, **kwargs):
    return _get_dagpath_list_from_type(ComponentList, *args, **kwargs)


def dagpls(*args, **kwargs):
    return _get_dagpath_list_from_type(DagpathList, *args, **kwargs)


def depnls(*args, **kwargs):
    return _get_dagpath_list_from_type(DependencyList, *args, **kwargs)


def plugls(name=None, *args, **kwargs):
    return _get_dagpath_list_from_type(PlugList, *args, **kwargs)


def get_comp(dagpath):
    return SingleIndexComponent(dagpath)
