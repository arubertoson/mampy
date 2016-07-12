"""
This module implements the Mampy API.

:copyright: (c) 2015 by Marcus Albertsson
:license: MIT, see LICENSE for more details.

"""
from mampy.dgcontainers import SelectionList, SelectionMask, OptionVar, MelGlobals
from mampy.dgcomps import Component
from mampy.dgnodes import DagNode

__all__ = ['selected', 'ls', 'ordered_selection', 'get_node', 'get_component',
           'optionVar', 'mel_globals', 'get_active_mask']


def selected():
    """
    Constructs and return a :class:`.SelectionList` from
    MGlobal.getActiveSelectionList()

    :rtype: :class:`.SelectionList`
    """
    return SelectionList.from_selection()


def ls(*args, **kwargs):
    """
    Constructs and return a :class:`.SelectionList` from given args,
    kwargs.

    Supports all parameters that cmds.ls have.

    :param \*args: dagpath or dagpath list.
    :param \*\*kwargs: Optional arguments that ``ls`` takes.
    :rtype: :class:`.SelectionList`

    Usage::

        >>> import mampy
        >>> slist = mampy.ls(sl=True, dag=True, type='mesh')
        SelectionList([u'pCubeShape1', u'pCubeShape2'])
    """
    return SelectionList.from_ls(*args, **kwargs)


def ordered_selection(slice_start=None, slice_stop=None, slice_step=None,
                      **kwargs):
    """
    Constructs and return an ordered :class:`.SelectionList`.

    :param slice_start: Where the slice starts from.
    :param slice_stop: Where the slice stops.
    :param slice_step: steps.
    :param \*\*kwargs: Optional arguments that ``ls`` takes.
    :rtype: :class:`.SelectionList`

    Usage::

        >>> import mampy
        >>> cmds.ls(sl=True)
        [u'pCube3', u'pCube2', u'pCube4', u'pCube1']
        >>> slist = mampy.ordered_selection(-2)
        [u'pCube4', u'pCube1']
    """
    return SelectionList.from_ordered(slice_start, slice_stop, slice_step,
                                      **kwargs)


def get_node(dagpath):
    """
    Construct and return a :class:`.DagNode` from given dagpath.

    :param dagpath: ``api.OpenMaya.MDagPath`` or dagpath str.
    :rtype: :class:`.DagNode`

    Usage::

        >>> dagpath = 'pCube1'
        >>> dagnode = get_node(dagpath)
        DagNode('pCube1')

    If support for a specific node exists DagNode will try to create
    it. These subclasses must be created manually and **always** have
    the same name as the ``cmds.nodeType`` return value from a dagpath.

        >>> dagpath = 'persp'
        >>> dagnode = get_node(dagpath)
        Camera('persp')
    """
    return DagNode(dagpath)


def get_component(dagpath):
    """
    Construct and return a :class:`Component` from given dagpath.

    :param dagpath: dagpath string or a list of dagpath strings
    :rtype: :class:`.Component`

    Usage::

        >>> dagpath = 'pCube1.f[4]'
        >>> component = Component(dagpath)
        Component(['pCube1.f[4]'])
    """
    return Component(dagpath)


def optionVar(*args, **kwargs):
    """
    Construct and return a :class:`.OptionVar` object from
    cmds.optionVar

    :rtype: :class:`.OptionVar`

    Usage::

        >>> options = mampy.optionVar()
        >>> options['new_option_variable'] = 20
        >>> options['new_option_variable']
        20
        >>> options['TrackOrderedSelection']
        True

    .. note:: Redundant
    """
    return OptionVar(*args, **kwargs)


def mel_globals(*args, **kwargs):
    return MelGlobals(*args, **kwargs)


def get_active_mask():
    """
    Construct and return :class:`.SelectionMask` object from active
    selection mode.

    :rtype: :class:`.SelectionMask`

    Usage::

        >>> smask = mampy.get_active_mask()
        # By default SelectionMask will show the internal values.
        SelectionMask([43, 36, 45, 62])
        ...
        >>> smask.mask_strings
        ['kSelectMeshComponents', 'kSelectFacets', 'kSelectMeshFaces',
         'kSelectComponentsMask']
        >>> smask.clear()
        >>> smask.set(kSelectSurfaces)

    .. note:: Redundant
    """
    return SelectionMask.active()


