"""
This module implements the Mampy API.

:copyright: (c) 2016 by Marcus Albertsson
:license: MIT, see LICENSE for more details.
"""
from __future__ import absolute_import, unicode_literals

from .core.dagnodes import Node, DependencyNode
from .core.components import SingleIndexComponent, get_component_from_string
from .core.selectionlist import ComponentList, DagpathList, DependencyList, PlugList


def _get_dagpath_list_from_type(list_object, *args, **kwargs):
    if not args and not kwargs:
        return list_object.from_selection()
    elif args and isinstance(args[0], basestring):
        return list_object.from_name(args[0])
    elif args and isinstance(args[0], (tuple, list, set)):
        return list_object(args[0])
    return list_object.from_ls(*args, **kwargs)


def complist(*args, **kwargs):
    return _get_dagpath_list_from_type(ComponentList, *args, **kwargs)


def daglist(*args, **kwargs):
    return _get_dagpath_list_from_type(DagpathList, *args, **kwargs)


def dependlist(*args, **kwargs):
    return _get_dagpath_list_from_type(DependencyList, *args, **kwargs)


def pluglist(name=None, *args, **kwargs):
    return _get_dagpath_list_from_type(PlugList, *args, **kwargs)


def get_depend_node(dagobject):
    return DependencyNode(dagobject)


def get_node(dagpath):
    return Node(dagpath)


def get_single_index_component(dagpath, object=None):
    if isinstance(dagpath, basestring):
        dagpath, object = get_component_from_string(dagpath)
    return SingleIndexComponent(dagpath, object)
