"""
    mampy
    ~~~~~

    mampy is a Maya library, written in python for easier functionality.

    The maya api in its current state is overly verbose and very cumbersome
    to work with.

    Although pymel does make it easier the overhead is way to much if you
    want to write anything that is a bit fast. This is not how I want to work,
    I want it to be easy and fast which made me do mampy.

    Mampy aims to be lightweight pymel, it uses a mix between the old and new
    maya api. Mostly to access the datatypes the new api provides that are
    much easier to work with in python.

    Features

        - SelectionList object that behaves like an immutable python
          list.
        - Component object for access to common tasks.
        - Node objects for access too common tasks.
        - OptionVar dict object, much like pymels optionVar dict.

"""

from mampy.utils import SelectionList, OptionVar
from mampy.component import Component
from mampy.nodes import DagNode
