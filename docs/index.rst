mampy
=====

.. module:: mampy
    :synopsis: Object-oriented filesystem paths

.. moduleauthor:: Marcus Albertsson <marcus.arubertoson@gmail.com>


The Autodesk Maya API in its current state is overly verbose and very
cumbersome to work with. Although pymel does a great job the overhead
is way too heavy for iterations. I wanted something faster, so I made
mampy.

Mampy aims to be lightweight pymel, it uses a mix between the old and
new Maya APIs. Mostly to access the datatypes the new API provides
which are easier to work with than the old api objects.

.. note::
    This package is a work in progress. Features are added when needed
    so classes are most likely incomplete. But this goes hand in hand
    with my lightweight philosophy, no need to create functions that
    *might* be useful one day.


User Guide
----------

This part of the documentation aims to get you started with mampy. It's
quite gritty and is not written as a step by step guide but tries to
introduce the basic usage.

.. toctree::
   :maxdepth: 2

   component



API Documentation
-----------------

If you are looking for information on a specific function, class or
method.

.. toctree::
   :maxdepth: 2

   api
