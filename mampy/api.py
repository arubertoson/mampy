# -*- coding: utf-8 -*-
"""
mampy.api

This module implements the Mampy API.

:copyright: (c) 2015 by Marcus Albertsson
:license: MIT, see LICENSE for more details.

"""

from .utils import OptionVar
from .selectionlist import SelectionList
from .component import Component
from .nodes import DagNode


def ls(*args, **kwargs):
    """Constructs and returns a :class:`.SelectionList` from given args, kwargs.

    Supports all parameters that cmds.ls have.

    :param \*\*kwargs: Optional arguments that ``ls`` takes.
    :return: :class:`.SelectionList` object.

    Usage::

        >>> import mampy
        >>> slist = mampy.ls(sl=True, type='mesh')
        ['']
    """
    return SelectionList.from_ls(*args, **kwargs)


def selected():
    """Constructs and returns a :class:`.SelectionList` from
    MGlobal.getActiveSelectionList()

    :return: :class:`.SelectionList` object.
    """
    return SelectionList.from_selection()


def ordered_selection(slice_start=None, slice_stop=None, slice_step=None,
                      **kwargs):
    """Constructs and returns an ordered :class:`.SelectionList`.

    :param slice_start: Where the slice starts from.
    :param slice_stop: Where the slice stops.
    :param slice_step: How many steps the slice jumps.
    :param \*\*kwargs: Optional arguments that ``ls`` takes.
    :return: :class:`.SelectionList` object.

    Usage::

        >>> import mampy
        >>> slist = mampy.ordered_selection(-2)
        ['']
    """
    return SelectionList.ordered_selection(slice_start, slice_stop, slice_step,
                                           **kwargs)


def get_node(dagpath):
    """Constructs and returns a :class:`.DagNode` from given dagpath.

    :param dagpath: MDagPath or basestring.
    :return: :class:`.DagNode`

    Usage::

        >>> dagpath = 'pCube1'
        >>> dagnode = DagNode(dagpath)
        DagNode('pCube1')
    """
    return DagNode(dagpath)


def get_component(dagpath):
    """Constructs and returns a :class:`Component` from given dagpath.

    :param dagpath: dagpath as basestring.
    :return: :class:`.Component`

    Usage::

        >>> dagpath = 'pCube1.f[4]'
        >>> component = Component(dagpath)
        Component(['pCube1.f[4]'])
    """
    return Component(dagpath)


def optionVar(*args, **kwargs):
    """Constructs and returns a :class:`.OptionVar` object from cmds.optionVar

    :return: :class:`.OptionVar`

    Usage::

        >>> import mampy
        >>> options = mampy.optionVar()
        >>> options['option_name']
        option_value
        >>> options['option_name'] = 20
    """
    return OptionVar(*args, **kwargs)
