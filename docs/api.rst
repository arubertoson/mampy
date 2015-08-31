.. _api:

API Documentation
=================

.. module:: mampy

Main Interface
--------------

All of mampys' functionality can be accessed by these functions. They
all return an instance of the main workhorses:

* :class:`SelectionList`
* :class:`Component`
* :class:`DagNode`


.. autofunction:: selected
.. autofunction:: ls

.. autofunction:: ordered_selection
.. important::

    It seems that Maya 2015 returns an ordered selection by default
    without having the track ordered selection option box.

.. autofunction:: get_node
.. autofunction:: get_component
.. autofunction:: optionVar



Classes
=======

.. _SelectionList:

Selection List
--------------

.. autoclass:: mampy.SelectionList
    :members:


DagNode
-------

.. autoclass:: mampy.DagNode
    :members:
.. autoclass:: mampy.Camera

Component
---------

.. autoclass:: mampy.Component
    :members:

.. autoclass:: mampy.comp.MeshVert
.. autoclass:: mampy.comp.MeshEdge
.. autoclass:: mampy.comp.MeshPolygon
.. autoclass:: mampy.comp.MeshMap
    :members:
