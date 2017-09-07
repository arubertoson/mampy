<project logo centered>

# Mampy - A simpler Maya API

The Maya API in it's current form is overly verbose and very cumbersome to work with. Although pymel does a great job the overhead is way too heavy for any form of iterations. **Mampy** is a Maya API adapter/wrapper that aims to achieve easier access to commonly used functionality when writing scripts or plug-ins for Maya.

<insert gif with simple usecase>

<div class="warning">
  <strong>NOTE:</strong>
</div>
Currently, as I am the only contributor mampy is quite limited in features and I only implement them on a need to basis. I am happy to take requests and for any help anyone is willing to give.

# Features

* Wraps complicated API functionality with an easy to use interface
* Provides helper algorithms for common problems
* External package pathlib2 to handle file system navigation

# Install

* Make **pip** available to **mayapy**. The easiest approach is to download `get-pip.py` from the official [source](https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip) and invoke command in console: `path/to/Autodesk/Maya<version>/bin/mayapy get-pip.py`
* `/path/to/Autodesk/Maya<version>/Python/Scripts/pip install mampy`


# Usage

To create a selection function that would flood (get all connected components) our current selection while also making it undoable and repeatable we could do something like this.

```python
from maya.api import OpenMaya

import mampy
from mampy.exceptions import InvalidSelectionWarning
from mampy.decorators import undoable, repeatable

@undoable
@repeatable
def flood():
    selected = mampy.complist.from_selected()
    if not selected:
        # Outputs linenumber and file for easy debugging
        mampy.warning("Please select component objects", InvalidSelectionWarning)
    else:
        flood = mampy.complist()
        for comp in selected:
            if comp.type == OpenMaya.MFn.kMeshMapComponent:
                shells = mampy.computils.getuvshells(comp)
            else:
                shells = mampy.computils.getmeshshells(comp)
            flood.update(shells)
        cmds.select(flood.cmdslist())
```

It's a sane way of working with python in maya.

# Contributors

* [Marcus Albertsson](https://github.com/arubertoson)

# License
Unless stated otherwise all works are:

    Copyright © 2015-2017 Marcus Albertsson

[MIT License](https://github.com/arubertoson/mampy/blob/master/LICENCE)
