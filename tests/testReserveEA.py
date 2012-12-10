#!/usr/bin/python
"""
Python tests for SCSI-3 Persistent Group Reservations

Description:
 This module tests Exclusive Access Reservations. See ... for more
 details.

TODO
 - ...
"""


__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


import sys
import os
import time

import unittest

from support.initiator import Initiator
from support.dprint import dprint
from support.cmd import verifyCmdExists, runCmdWithOutput
from support.reservation import ProutTypes, Reservation

#
# config stuff ...
#

################################################################

# XXX Fix this -- these need to be global options

# options
class Opts:
    pass

Opts.debug = os.getenv("TR_DEBUG")

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

def my_resvn_setup():
    """make sure we are all setup to test reservations"""
    if initA.unregister() != 0:
        initA.unregister()
    if initB.unregister() != 0:
        initB.unregister()
    initA.register()
    initB.register()

################################################################

class Test01CanReserveEaTestCase(unittest.TestCase):
    """Test that PGR RESERVE Exclusive Access can be set"""

    def setUp(self):
        my_resvn_setup()

    def testCanReserveEa(self):
        res = initA.reserve(ProutTypes["ExclusiveAccess"])
        self.assertEqual(res, 0)

################################################################

class Test02CanReadEaReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Exclusive Access can be read"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["ExclusiveAccess"])

    def testCanReadReservationFromReserver(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
 
    def testCanReadReservationFromNonReserver(self):
        resvnB = initB.getReservation()
        self.assertEqual(resvnB.key, initA.key)
        self.assertEqual(resvnB.getRtypeNum(), ProutTypes["ExclusiveAccess"])

################################################################

class Test03CanReleseEaReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Exclusive Access can be released"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["ExclusiveAccess"])

    def testCanReleaseReservation(self):
        time.sleep(2)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = initA.release(ProutTypes["ExclusiveAccess"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def testCannotReleaseReservation(self):
        time.sleep(2)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = initB.release(ProutTypes["ExclusiveAccess"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])

################################################################

class Test04UnregisterEaHandlingTestCase(unittest.TestCase):
    """Test how PGR RESERVE Exclusive Access reservation is handled
    during unregistration"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["ExclusiveAccess"])

    def testUnregisterReleasesReservation(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = initA.unregister()
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def testUnregisterDoesNotReleaseReservation(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = initB.unregister()
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])

################################################################

class Test05ReservationEaAccessTestCase(unittest.TestCase):
    """Test how PGR RESERVE Exclusive Access reservation acccess is
    handled"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["ExclusiveAccess"])

    def testReservationHolderHasReadAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        # initA read from disk to /dev/null
        ret = runCmdWithOutput(["dd", "if=" + initA.dev, "of=/dev/null",
                                "bs=512", "count=1"], Opts)
        self.assertEqual(ret.result, 0)
        
    def testReservationHolderHasWriteAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        # initA can write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initA.dev,
                                "bs=512", "seek=1", "count=1"], Opts)
        self.assertEqual(ret.result, 0)
    
    def testNonReservationHolderDoesNotHaveReadAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        # initA get reservation
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        # initB can't read from disk to /dev/null
        ret = runCmdWithOutput(["dd", "if=" + initB.dev, "of=/dev/null",
                                "bs=512", "count=1"], Opts)
        self.assertEqual(ret.result, 1)

    def testNonReservationHolderDoesNotHaveWriteAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        # initA get reservation
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        # initB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initB.dev,
                                "bs=512", "seek=1", "count=1"], Opts)
        self.assertEqual(ret.result, 1)
