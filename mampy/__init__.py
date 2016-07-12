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
__version__ = '0.1.1'
__license__ = 'MIT'


from mampy.api import *
