=======================
Working with Components
=======================

.. module:: mampy.comp

.. note::

    This document is a work in progress. It's always advisable to look
    through the source, if you still can't find your answer the feature
    you are looking for might not be implemented. Send me and email or
    join the development.


A component is a container of a Maya `component set`. Each component is
a Python class that subclasses :class:`.Component` and currently only
supports components found on Maya mesh object.


Quick example
=============

This example shows how components are usually fetched within mampy.
From the API function :func:`mampy.selected` we create a
:class:`.SelectionList` containing the currently selected objects in
    Maya. We then fetch the components from that list.

    >>> import mampy
    ...
    >>> slist = mampy.selected()
    >>> components = list(slist.itercomps())
    [MeshVert([u'pCube1.vtx[0]', u'pCube1.vtx[2:5]']),
     MeshVert([u'pCube2.vtx[0]', u'pCube2.vtx[2]'])]


As you can see a component is not a single index of a vertex, it is a
set of components belonging to a certain object. This is useful
knowledge because that means we can create components and add to them.
To create an empty component we must provide a valid Maya dagpath to
either subclasses: :class:`MeshVert`, :class:`MeshEdge`,
:class:`MeshPolygon` or :class:`MeshMap` or we can use
:func:`Component.create() <mampy.Component.create()>`, but then we must
provide the Mayas internal *int type* for the component we want to
create.

    >>> from maya.OpenMaya import MFn
    >>> dagpath = 'pCube1'
    >>> vert = mampy.Component(dagpath, MFn.kMeshVertComponent)
    MeshVert('pCube1.vtx[]')

This is not the preferred way of creating components. It's much easier
and clearer to do this:

    >>> dagpath = 'pCube1'
    >>> vert = MeshVert(dagpath)
    MeshVert('pCube1.vtx[]')

From an empty component object you can quickly get something useful by
either adding indices to it or just get the complete component:

    >>> vert.add([1, 2, 3])
    MeshVert('pCube1.vtx[1:3]')
    ...
    >>> vert.add(5)
    MeshVert(['pCube1.vtx[1:3]', 'pCube1.vtx[5]'])
    ...
    >>> complete = vert.get_complete()
    MeshVert('pCube1.vtx[*]')

Then we can easily send the component object to a normal ``maya.cmds``
function not how we call ``list()`` on the :class:`.Component` to
retrieve a Maya *string list* representing the component set:

    >>> cmds.select(list(vert), r=True)
    >>> cmds.ls(sl=True)
    ['pCube1.vtx[1:3]', 'pCube1.vtx[5]']
    ...
    >>> cmds.select(list(complete), r=True)
    >>> cmds.ls(sl=True)
    ['pCube1.vtx[*]']


Other ways to fetch a :class:`.Component` through the API is the
:func:`mampy.get_component` function. Now that we know how components
are constructed we can pass a Maya *string list* to the function:

    >>> slist = cmds.ls(sl=True)
    [u'pCube1.vtx[2:4]', u'pCube1.vtx[7]']
    >>> comp = mampy.get_component(slist)
    MeshVert([u'pCube1.vtx[2:4]', u'pCube1.vtx[7]'])

Something of note, we can't pass more than one component into the
:func:`mampy.get_component()` function, it's only meant to create a
single :class:`.Component` object:

    >>> slist = cmds.sl(sl=True)
    # From the dagpaths we can see that we are working with two objects.
    [u'pCube1.vtx[2:4]', u'pCube1.vtx[7]', u'pCube2.vtx[5]']
    >>> comp = mampy.get_component(slist)
    TypeError: More than one object in dagpath.



The :doc:`API <api>` documentation provides additional information
about the different :class:`.Component` functions and attributes.
