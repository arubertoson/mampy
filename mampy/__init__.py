"""
Mampy Maya library

Mampy is a Maya API wrapper, written in python. The maya api is overly
cumbersome to use and not kind to the python sanity, this inspired
mampy.

Basig Usage::

    >>> import mampy
    >>> slist = mampy.selected()
    >>> component = slist.itercomps()
    ['list of components']
    >>> cmds.select(list(components), r=True)

or to work with a Node::

    >>> name = 'persp'
    >>> camera = DagNode(name)
    >>> camera.get_shape()
    'perspShape'


For more examples see documentation at <http://readthedocs.com>.

:copyright: (c) 2015 Marcus Albertsson.
:license: MIT, see LICENSE for more details.
"""

from mampy.utils import *
from mampy.slist import *
from mampy.node import *
from mampy.comp import *
from mampy.packages.mvp import Viewport, RenderGlobals
from mampy.api import (ls, selected, ordered_selection, get_node,
                       get_component, optionVar, get_active_mask)


__title__ = 'mampy'
__version__ = '0.0.2'
__author__ = 'Marcus Albertsson'
__email__ = 'marcus.arubertoson@gmail.com'
__url__ = 'http://github.com/arubertoson/maya-mampy'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Marcus Albertsson'
