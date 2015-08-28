"""
    Mampy Maya library
    ~~~~~~~~~~~~~~~~~~

    Mampy is a Maya API wrapper, written in python. Basic usage:

        >>> import mampy
        >>> slist = mampy.selected()
        >>> component = slist.itercomps()
        ['list of components']
        >>> cmds.select(list(components), r=True)

    or to work with a Node:

        >>> name = 'persp'
        >>> camera = DagNode(name)
        >>> camera.get_shape()
        'perspShape'


    For more examples see documentation at <http://readthedocs.com>.

    :copyright: (c) 2015 Marcus Albertsson.
    :license: MIT, see LICENSE for more details.

"""

from . import utils
from .selectionlist import SelectionList
from .node import DagNode
from .component import Component
from .api import (ls, selected, ordered_selection, get_node, get_component,
                  optionVar)
