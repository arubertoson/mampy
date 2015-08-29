.. mampy documentation master file, created by
   sphinx-quickstart on Sat Aug 29 01:12:51 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mampy
=====

.. module:: mampy
    :synopsis: Object-oriented filesystem paths

.. moduleauthor:: Marcus Albertsson <marcus.arubertoson@gmail.com>


The maya api in its current state is overly verbose and very cumbersome
to work with. Although pymel does a great job the overhead is way
too heavy for iterations. I wanted something faster, so I made mampy.

Mampy aims to be lightweight pymel, it uses a mix between the old and new
maya api. Mostly to access the datatypes the new api provides which are
way easier to work with than the old api objects.

.. note::
    This module is a work in progress. I usually add features as I need them
    so classes are most likely incomplete. But this goes hand in hand with
    my lightweight philosophy. No need to bloat it to death!

Download
--------

Main development takes place on github: http://github.com/arubertoson/maya-mampy


Basic use
---------

Importing the module::

    >>> import mampy

Listing selected objects:

    >>> s = mampy.selected()
    >>> s
    ('mampy_1_mesh', 'mampy_curve')

Listing mesh objects in selection:

    >>> s = mampy.ls(sl=True, type='mesh')
    >>> s
    ('mampy_1_mesh')


Contents:

.. toctree::
   :maxdepth: 2

.. autofunction:: selected


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
