#!/usr/bin/python
"""
Python tests for SCSI-3 Persistent Group Reservations

Description:
 This module tests Registration. See ... for more details.


TODO
 - ...
"""


__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


import sys
import os
import copy

import unittest

from support.initiator import Initiator
from support.dprint import dprint
from support.cmd import verifyCmdExists

################################################################

# XXX Fix this -- these need to be global options

# options
class Opts:
    pass

Opts.debug = os.getenv("TR_DEBUG", False)

dprint(Opts, "XXX testing at module init time ...")

################################################################

#
# our 2 initiators
#
# these are set up statically and must be created manually ahead
# of time
#

# XXX Fix this!

initA = Initiator("t1", "/dev/sdc", "0x123abc", Opts)
initB = Initiator("t2", "/dev/sdd", "0x696969", Opts)

################################################################


def setUpModule():
    """Whole-module setup -- not yet used?"""
    dprint(Opts, "Module-level setup ...")
    if os.geteuid() != 0:
        print >>sys.stderr, "Fatal: must be root to run this script\n"
        sys.exit(1)
    verifyCmdExists(["sg_persist", "-V"], Opts)
    verifyCmdExists(["sg_inq", "-V"], Opts)
    verifyCmdExists(["dd", "--version"], Opts)
    # make sure all devices are the same
    iiA = initA.getDiskInquirySn()
    iiB = initB.getDiskInquirySn()
    if not iiA or not iiB:
        print >>sys.stderr, \
              "Fatal: cannot get INQUIRY data from %s or %s\n" % \
              (initA.dev, initB.dev)
        sys.exit(1)
    if iiA != iiB:
        print >>sys.stderr, \
              "Fatal: Serial numbers differ for %s and %s\n" % \
              (initA.dev, initB.dev)
        sys.exit(1)

################################################################


class Test01CanRegisterTestCase(unittest.TestCase):
    """Can register initiators"""

    def setUp(self):
        """Set up for tests"""
        initA.clear()
        initB.clear()

    def testCanRegisterInitA(self):
        resA = initA.register()
        self.assertEqual(resA, 0)

    def testCanRegisterInitB(self):
        resB = initB.register()
        self.assertEqual(resB, 0)


################################################################

class Test02CanSeeRegistrationsTestCase(unittest.TestCase):
    """Can see initiator registration"""

    def setUp(self):
        res = initA.clear()
        res = initB.clear()

    def testCanSeeNoRegistrations(self):
        registrantsA = initA.getRegistrants()
        self.assertEqual(len(registrantsA), 0)

    def testCanSeeRegistration(self):
        res = initA.register()
        self.assertEqual(res, 0)
        res = initB.register()
        self.assertEqual(res, 0)
        registrantsA = initA.getRegistrants()
        self.assertEqual(len(registrantsA), 2)
        self.assertEqual(registrantsA[0], initA.key)
        self.assertEqual(registrantsA[1], initB.key)

    def testCanSeeRegOnDifferentInit(self):
        resA = initA.register()
        self.assertEqual(resA, 0)
        registrantsB = initB.getRegistrants()
        self.assertEqual(len(registrantsB), 1)
        self.assertEqual(registrantsB[0], initA.key)

################################################################

class Test03CanUnregisterTestCase(unittest.TestCase):
    """Can Unregister"""

    def setUp(self):
        initA.clear()
        initB.clear()
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

class Test04ReregistrationFailsTestCase(unittest.TestCase):
    """Cannot reregister"""

    def setUp(self):
        initA.clear()
        initB.clear()
        initA.register()
        initB.register()

    def testReregisterFails(self):
        initAcopy = copy.copy(initA)
        initAcopy.key = "0x1"
        resA = initAcopy.register()
        self.assertNotEqual(resA, 0)
        registrantsA = initA.getRegistrants()
        self.assertEqual(len(registrantsA), 2)
        self.assertEqual(registrantsA[0], initA.key)
        self.assertEqual(registrantsA[1], initB.key)


################################################################

class Test05RegisterAndIgnoreTestCase(unittest.TestCase):
    """Can Register And Ignore"""

    def setUp(self):
        initA.clear()
        initB.clear()
        initA.register()
        initB.register()

    def testCanRegisterAndIgnore(self):
        # register with key "0x1"
        initAcopy = copy.copy(initA)
        initAcopy.key = "0x1"
        result = initA.registerAndIgnore(initAcopy.key)
        self.assertEqual(result, 0)
        registrantsA = initAcopy.getRegistrants()
        self.assertEqual(registrantsA[0], initAcopy.key)
        # re-register with normal key
        result = initAcopy.registerAndIgnore(initA.key)
        self.assertEqual(result, 0)
        registrantsA = initA.getRegistrants()
        self.assertEqual(registrantsA[0], initA.key)
