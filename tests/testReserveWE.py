#!/usr/bin/python
"""
Python tests for SCSI-3 Persistent Group Reservations

Description:
 This module tests Write Exclusive Reservations. See ... for more
 details.

TODO
 - ...
"""


__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


import sys
import os
import time

import unittest

from support.initiator import initA, initB, initC
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

def setUpModule():
    """Whole-module setup -- not yet used?"""
    dprint(Opts, "Module-level setup ...")
    if os.geteuid() != 0:
        print >>sys.stderr, "Fatal: must be root to run this script\n"
        sys.exit(1)
    verifyCmdExists(["sg_persist", "-V"], Opts)
    verifyCmdExists(["sg_inq", "-V"], Opts)
    verifyCmdExists(["dd", "--version"], Opts)
    verifyCmdExists(["sg_turs", "--version"], Opts)
    # make sure all devices are the same
    iiA = initA.getDiskInquirySn()
    iiB = initB.getDiskInquirySn()
    iiC = initC.getDiskInquirySn()
    if not iiA or not iiB or not iiC:
        print >>sys.stderr, \
              "Fatal: cannot get INQUIRY data from %s, %s or %s\n" % \
              (initA.dev, initB.dev, initC.dev)
        sys.exit(1)
    if iiA != iiB or iiA != iiC:
        print >>sys.stderr, \
              "Fatal: Serial numbers differ for %s, %s or %s\n" % \
              (initA.dev, initB.dev, initC.dev)
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
    initC.runTur()

################################################################

class TC01CanReserveWeTestCase(unittest.TestCase):
    """Test PGR RESERVE Write Exclusive can be set"""

    def setUp(self):
        my_resvn_setup()
        self.rtype = ProutTypes["WriteExclusive"]

    def testCanReserve(self):
        res = initA.reserve(self.rtype)
        self.assertEqual(res, 0)

################################################################

class TC02CanReadWeReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive can be read"""

    def setUp(self):
        my_resvn_setup()
        self.rtype = ProutTypes["WriteExclusive"]
        initA.reserve(self.rtype)

    def testCanReadReservationFromReserver(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)

    def testCanReadReservationFromNonReserver(self):
        resvnB = initB.getReservation()
        self.assertEqual(resvnB.key, initA.key)
        self.assertEqual(resvnB.getRtypeNum(), self.rtype)

    def testCanReadReservationFromNonRegistrant(self):
        resvnC = initC.getReservation()
        self.assertEqual(resvnC.key, initA.key)
        self.assertEqual(resvnC.getRtypeNum(), self.rtype)

################################################################

class TC03CanReleaseWeReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive can be released"""

    def setUp(self):
        my_resvn_setup()
        self.rtype = ProutTypes["WriteExclusive"]
        initA.reserve(self.rtype)

    def testReservationHolderCanReleaseReservation(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        res = initA.release(self.rtype)
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def testNonReservationHolderCannotReleaseReservation(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        res = initB.release(self.rtype)
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)

################################################################

class TC04UnregisterWeHandlingTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive reservation is handled
    during unregistration"""

    def setUp(self):
        my_resvn_setup()
        self.rtype = ProutTypes["WriteExclusive"]
        initA.reserve(self.rtype)

    def testReservationHolderUnregisterReleasesReservation(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        res = initA.unregister()
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def testNoneReservationHolderUnregisterDoesNotReleaseReservation(self):
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        res = initB.unregister()
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)

################################################################

class TC05ReservationWeAccessTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive reservation access is
    handled"""

    def setUp(self):
        my_resvn_setup()
        self.rtype = ProutTypes["WriteExclusive"]
        initA.reserve(self.rtype)

    def testReservationHolderHasReadAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        # initA read from disk to /dev/null
        ret = runCmdWithOutput(["dd",
                                "if=" + initA.dev,
                                "iflag=direct",
                                "of=/dev/null",
                                "bs=512",
                                "count=1"],
                               Opts)
        self.assertEqual(ret.result, 0)

    def testReservationHolderHasWriteAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        # initA write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd",
                                "if=/dev/zero",
                                "of=" + initA.dev,
                                "oflag=direct",
                                "bs=512",
                                "seek=1",
                                "count=1"],
                               Opts)
        self.assertEqual(ret.result, 0)
    
    def testNonReservationHolderDoesHaveReadAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        # initB can read from disk to /dev/null
        ret = runCmdWithOutput(["dd",
                                "if=" + initB.dev,
                                "iflag=direct",
                                "of=/dev/null",
                                "bs=512",
                                "count=1"],
                               Opts)
        self.assertEqual(ret.result, 0)
        
    def testNonReservationHolderDoesNotHaveWriteAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        # initB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd",
                                "if=/dev/zero",
                                "of=" + initB.dev,
                                "oflag=direct",
                                "bs=512",
                                "seek=1",
                                "count=1"],
                               Opts)
        self.assertEqual(ret.result, 1)

    def testNonRegistrantDoesHaveReadAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        # initC can read from disk to /dev/null
        ret = runCmdWithOutput(["dd",
                                "if=" + initC.dev,
                                "iflag=direct",
                                "of=/dev/null",
                                "bs=512",
                                "count=1"],
                               Opts)
        self.assertEqual(ret.result, 0)
        
    def testNonRegistrantDoesNotHaveWriteAccess(self):
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), self.rtype)
        # initC can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd",
                                "if=/dev/zero",
                                "of=" + initC.dev,
                                "oflag=direct",
                                "bs=512",
                                "seek=1",
                                "count=1"],
                               Opts)
        self.assertEqual(ret.result, 1)
