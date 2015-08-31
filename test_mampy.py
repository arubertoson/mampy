#! C:\Program Files\Autodesk\Maya2015\bin\mayapy
# -*- coding: utf-8 -*-

"""Tests for mampy."""

import os
import logging
import unittest

import maya.standalone
import maya.cmds as cmds

import mampy

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


test_ma_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_mampy.ma')


class TestSelectionList(unittest.TestCase):

    def setUp(self):
        """Setup maya for test case."""
        maya.standalone.initialize(name='python')
        cmds.file(test_ma_file, force=True, open=True)
        self.slist = mampy.slist.SelectionList

    def test_creation(self):
        self.assertIsInstance(self.slist(), mampy.slist.SelectionList)

    def test_from_selection(self):
        cmds.select(cmds.ls(type='mesh'))
        slist = self.slist.from_selection()
        self.assertTrue(slist)

    def test_from_ls(self):
        slist = self.slist.from_ls(type='mesh')
        self.assertTrue(slist)

    def test_from_ordered(self):
        obj1, obj2 = 'mampy_1_mesh', 'mampy_2_mesh'
        cmds.select(obj1), cmds.select(obj2, add=True)
        slist = self.slist.from_ordered()
        self.assertEqual(len(slist), 2)
        self.assertTrue(str(slist[0]), obj1)
        self.assertTrue(str(slist[1]), obj2)

    def test_from_ordered_slice(self):
        obj1, obj2, obj3 = 'mampy_1_mesh', 'mampy_2_mesh', 'mampy_3_mesh'
        cmds.select(obj1, r=True), cmds.select(obj2, obj3, add=True)
        slist = self.slist.from_ordered(-2)
        self.assertEqual(len(slist), 2)
        self.assertTrue(str(slist[0]), obj2)
        self.assertTrue(str(slist[1]), obj3)

    def test_nonzero_false(self):
        slist = self.slist()
        self.assertFalse(slist)

    def test_nonzero_true(self):
        cmds.select(cmds.ls(type='mesh'))
        slist = self.slist.from_selection()
        self.assertTrue(slist)

    def test_str_output(self):
        slist = self.slist.from_ls(transforms=True)
        self.assertIsInstance(str(slist), basestring)

    def test_iter_output(self):
        slist = self.slist.from_ls(transforms=True)
        self.assertIsInstance(list(slist), list)
        self.assertIsInstance(list(slist)[0], basestring)

    def test_append(self):
        slist = self.slist()
        mesh = 'mampy_1_mesh'
        slist.append(mesh)



if __name__ == '__main__':
    unittest.main()
