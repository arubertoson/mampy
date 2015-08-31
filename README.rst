==================
A simpler Maya API
==================
mampy is a Maya library, written in python for easier functionality.

The maya api in its current state is overly verbose and very cumbersome
to work with. Although pymel does a great job the overhead is way too
heavy for iterations. I wanted something faster, so I made mampy.

Mampy aims to be lightweight pymel, it uses a mix between the old and
new maya api. Mostly to access the datatypes the new api provides which
are way easier to work with than the old api objects.

Note that mampy is a work in progress and currently only have a very
limited amount of features.

Features
========

    * :class:`SelectionList` object that behaves like an immutable
        python list.
    * :class:`Component` object for access to common tasks.
    * :class:`DagNode` objects for access too common tasks.
    * :class:`OptionVar` dict object, much like pymels optionVar dict.


Documentation
=============

For more information visit
`docs <http://maya-mampy.readthedocs.org/en/latest>`_.
