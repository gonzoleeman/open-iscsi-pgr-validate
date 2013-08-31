#!/usr/bin/python
"""
Python tests for SCSI-3 Persistent Group Reservations

Description:
 This module tests Registration. See ... for more details.
"""


__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


import sys
import os
from copy import copy
import unittest

from support.initiator import initA, initB, initC
from support.setup import set_up_module

################################################################

def setUpModule():
    """Whole-module setup"""
    set_up_module(initA, initB, initC)

################################################################

def my_reg_setup():
    """make sure we are all setup to test reservations"""
    if initA.unregister() != 0:
        initA.unregister()
    if initB.unregister() != 0:
        initB.unregister()
    initC.runTur()

################################################################

class test01CanRegisterTestCase(unittest.TestCase):
    """Can register initiators"""

    def setUp(self):
        my_reg_setup()

    def testCanRegisterInitA(self):
        resA = initA.register()
        self.assertEqual(resA, 0)

    def testCanRegisterInitB(self):
        resB = initB.register()
        self.assertEqual(resB, 0)

################################################################

class test02CanSeeRegistrationsTestCase(unittest.TestCase):
    """Can see initiator registration"""

    def setUp(self):
        my_reg_setup()

    def testCanSeeNoRegistrations(self):
        registrantsA = initA.getRegistrants()
        self.assertEqual(len(registrantsA), 0)

    def testCanSeeRegistrationOnFirstRegistrant(self):
        res = initA.register()
        self.assertEqual(res, 0)
        res = initB.register()
        self.assertEqual(res, 0)
        registrantsA = initA.getRegistrants()
        self.assertEqual(len(registrantsA), 2)
        self.assertIn(initA.key, registrantsA)
        self.assertIn(initB.key, registrantsA)

    def testCanSeeRegOnSecondRegistrant(self):
        resA = initA.register()
        self.assertEqual(resA, 0)
        res = initB.register()
        self.assertEqual(res, 0)
        registrantsB = initB.getRegistrants()
        self.assertEqual(len(registrantsB), 2)
        self.assertIn(initA.key, registrantsB)
        self.assertIn(initB.key, registrantsB)

    def testCanSeeRegOnNonRegistrant(self):
        resA = initA.register()
        self.assertEqual(resA, 0)
        res = initB.register()
        self.assertEqual(res, 0)
        registrantsC = initC.getRegistrants()
        self.assertEqual(len(registrantsC), 2)
        self.assertIn(initA.key, registrantsC)
        self.assertIn(initB.key, registrantsC)

################################################################

class test03CanUnregisterTestCase(unittest.TestCase):
    """Can Unregister"""

    def setUp(self):
        my_reg_setup()
        initA.register()
        initB.register()

    def testCanUnregister(self):
        res = initA.unregister()
        self.assertEqual(res, 0)
        registrants = initA.getRegistrants()
        self.assertEqual(len(registrants), 1)
        res = initB.unregister()
        self.assertEqual(res, 0)
        registrants = initB.getRegistrants()
        self.assertEqual(len(registrants), 0)

################################################################

class test04ReregistrationFailsTestCase(unittest.TestCase):
    """Cannot reregister"""

    def setUp(self):
        my_reg_setup()
        initA.register()
        initB.register()

    def testReregisterFails(self):
        initAcopy = copy(initA)
        initAcopy.key = "0x1"
        resA = initAcopy.register()
        self.assertNotEqual(resA, 0)
        registrantsA = initA.getRegistrants()
        self.assertEqual(len(registrantsA), 2)
        self.assertIn(initA.key, registrantsA)
        self.assertIn(initB.key, registrantsA)

################################################################

class test05RegisterAndIgnoreTestCase(unittest.TestCase):
    """Can Register And Ignore"""

    def setUp(self):
        my_reg_setup()
        initA.register()
        initB.register()

    def testCanRegisterAndIgnore(self):
        # register with key "0x1"
        initAcopy = copy(initA)
        initAcopy.key = "0x1"
        result = initA.registerAndIgnore(initAcopy.key)
        self.assertEqual(result, 0)
        registrantsA = initAcopy.getRegistrants()
        self.assertNotIn(initA.key, registrantsA)
        self.assertIn(initAcopy.key, registrantsA)
        # re-register with normal key
        result = initAcopy.registerAndIgnore(initA.key)
        self.assertEqual(result, 0)
        registrantsA = initA.getRegistrants()
        self.assertNotIn(initAcopy.key, registrantsA)
        self.assertIn(initA.key, registrantsA)
