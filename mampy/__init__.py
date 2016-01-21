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

:copyright: (c) 2016 Marcus Albertsson.
:license: MIT, see LICENSE for more details.
"""

__author__ = 'Marcus Albertsson <marcus.arubertoson@gmail.com>'
__copyright__ = 'Copyright 2016 Marcus Albertsson'
__url__ = 'http://github.com/arubertoson/maya-mampy'
__version__ = '0.0.4'
__license__ = 'MIT'


from mampy.utils import *
from mampy.slist import *
from mampy.node import *
from mampy.comp import *
from mampy.datatypes import *
from mampy.exceptions import *
from mampy.packages.mvp import Viewport, RenderGlobals
from mampy.packages.pathlib import Path
from mampy.packages import profilehooks
from mampy.api import (ls, selected, ordered_selection, get_node,
                       get_component, optionVar, get_active_mask)


# Init
option_var = OptionVar()
mel_globals = MelGlobals()
