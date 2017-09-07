# -*- coding: utf-8 -*-
"""
General helper functions and pytest setup for test session.
"""
import os
import sys
import random
import contextlib

import pytest

from maya import cmds
import maya.api.OpenMaya as om
import maya.standalone


def match_pythonpath_to_syspath():
    # If testing a maya module make sure PYTHONPATH and sys.path are
    # identical
    realsyspath = [os.path.realpath(path) for path in sys.path]
    pythonpath = os.environ.get('PYTHONPATH', '')
    for p in pythonpath.split(os.pathsep):
        p = os.path.realpath(p)
        if p not in realsyspath:
            sys.path.insert(0, p)


def maya_standalone_teardown():
    # Starting Maya 2016, we have to call uninitialize
    if float(cmds.about(v=True)) >= 2016.0:
        maya.standalone.uninitialize()


@pytest.fixture(scope='session', autouse=True)
def maya_standalone(request):
    """ Every session needs to be initialized with maya standalone to tell
    maya that we are working without an interface while keeping maya
    behaviour.
    """
    maya.standalone.initialize()
    match_pythonpath_to_syspath()
    request.addfinalizer(maya_standalone_teardown)


@pytest.fixture(scope='function', autouse=True)
def newscene():
    """Run every test in a new Maya Scene for clean test environment."""
    cmds.file(f=True, new=True)


@pytest.fixture(scope='function')
def xcubes():

    @contextlib.contextmanager
    def _xcubes(num):
        dagpaths = []
        try:
            for _ in xrange(num):
                cube, _ = cmds.polyCube()
                dagpaths.append(cube)
            yield dagpaths
        finally:
            pass

    return _xcubes


def random_component():
    return random.choice(['vtx', 'e', 'map', 'f'])


@pytest.fixture(scope='function')
def xcomponents():

    @contextlib.contextmanager
    def _xcomponents(num):
        components = []
        try:
            for _ in xrange(num):
                component = ''.join(
                    [cmds.polyCube()[0], '.',
                     random_component(), '[*]'])
                components.append(component)
            yield components
        finally:
            pass

    return _xcomponents


@pytest.fixture(scope='function')
def maya_component():

    @contextlib.contextmanager
    def _maya_component(type=None):
        type = type or random_component()
        strcomp = ''.join([cmds.polyCube()[0], '.', type, '[*]'])
        try:
            yield om.MSelectionList().add(strcomp).getComponent(0)
        finally:
            pass

    return _maya_component


@pytest.fixture(scope='function')
def maya_dagpath():

    @contextlib.contextmanager
    def _maya_dagpath(name='test_cube'):
        strdag = cmds.polyCube(n=name)[0]
        try:
            yield om.MSelectionList().add(strdag).getDagPath(0)
        finally:
            pass

    return _maya_dagpath


@pytest.fixture(scope='function')
def maya_depnode():

    @contextlib.contextmanager
    def _maya_depnode():
        strdep = cmds.polyCube()[1]
        try:
            yield om.MSelectionList().add(strdep).getDependNode(0)
        finally:
            pass

    return _maya_depnode


@pytest.fixture(scope='function')
def maya_plug():

    @contextlib.contextmanager
    def _maya_plug():
        strdep = cmds.polyCube()[1] + '.depth'
        try:
            yield om.MSelectionList().add(strdep).getPlug(0)
        finally:
            pass

    return _maya_plug


@pytest.fixture(scope='function')
def complist(xcomponents):
    mlist = om.MSelectionList()
    with xcomponents(10) as complist:
        for each in complist:
            mlist.add(each)
        yield mlist


@pytest.fixture(scope='function')
def daglist(xcubes):
    mlist = om.MSelectionList()
    with xcubes(10) as daglist:
        for each in daglist:
            mlist.add(each)
        yield mlist


@pytest.fixture(scope='function')
def deplist(maya_depnode):
    mlist = om.MSelectionList()
    for _ in xrange(10):
        with maya_depnode() as depnode:
            mlist.add(depnode)
    yield mlist


@pytest.fixture(scope='function')
def pluglist(maya_plug):
    mlist = om.MSelectionList()
    for _ in xrange(10):
        with maya_plug() as plug:
            mlist.add(plug)
    yield mlist


# @pytest.fixture(scope='function')
# def nonsolid(xcubes):

#     @contextlib.contextmanager
#     def _nonsolid(name='test_cube'):
#         cube, node = cmds.polyCube(n=name)
#         cmds.setAttr(node + ".subdivisionsHeight", 2)
#         cmds.setAttr(node + ".subdivisionsDepth", 2)
#         cmds.delete(cube + '.f[3:4]')
#         try:
#             yield om.MSelectionList().add(cube).getDagPath(0)
#         finally:
#             cmds.delete(cube)

#     return _nonsolid
