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
    return True

################################################################

class Test01CanReserveWeTestCase(unittest.TestCase):
    """Test PGR RESERVE Write Exclusive can be set"""

    def setUp(self):
        my_resvn_setup()

    def testCanReserve(self):
        """Can reserve a target for exclusive access"""
        res = initA.reserve(ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)

################################################################

class Test02CanReadWeReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive can be read"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["WriteExclusive"])

    def testCanReadReservationFromReserver(self):
        """Can read WE reservation from reserving host"""
        res = initA.reserve(ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])

    def testCanReadReservationFromNonReserver(self):
        """Can read WE reservation from non-reserving host"""
        resvnB = initB.getReservation()
        self.assertEqual(resvnB.key, initA.key)
        self.assertEqual(resvnB.getRtypeNum(), ProutTypes["WriteExclusive"])

################################################################

class Test03CanReleaseWeReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive can be released"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["WriteExclusive"])

    def testCanReleaseReservation(self):
        """Can release a WE reservation from reserving host"""
        res = initA.reserve(ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = initA.release(ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def testCannotReleaseReservation(self):
        """Cannot release a WE reservation from non-reserving host"""
        res = initA.reserve(ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = initB.release(ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])

################################################################

class Test04UnregisterWeHandlingTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive reservation is handled
    during unregistration"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["WriteExclusive"])

    def testUnregisterReleasesReservation(self):
        """Un-registration of reserving WE host releases reservation"""
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = initA.unregister()
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def testUnregisterDoesNotReleaseReservation(self):
        """Un-registration of non-reserving WE host does not release
        reservation"""
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = initB.unregister()
        self.assertEqual(res, 0)
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])

################################################################

class Test05ReservationWeAccessTestCase(unittest.TestCase):
    """Test that PGR RESERVE Write Exclusive reservation access is
    handled"""

    def setUp(self):
        my_resvn_setup()
        initA.reserve(ProutTypes["WriteExclusive"])

    def testReservationHolderHasReadAccess(self):
        """The Reservation Holder has read access to the WE target"""
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        # initA read from disk to /dev/null
        ret = runCmdWithOutput(["dd", "if=" + initA.dev, "of=/dev/null",
                                "bs=512", "count=1"], Opts)
        self.assertEqual(ret.result, 0)

    def testReservationHolderHasWriteAccess(self):
        """The Reservation Holder has write access to the WE target"""
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        # initA write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initA.dev,
                                "bs=512", "seek=1", "count=1"], Opts)
        self.assertEqual(ret.result, 0)
    
    def testNonReservationHolderDoesHaveReadAccess(self):
        """Non-Reservation Holders have read access to the WE target"""
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        # initB can read from disk to /dev/null
        ret = runCmdWithOutput(["dd", "if=" + initB.dev, "of=/dev/null",
                                "bs=512", "count=1"], Opts)
        self.assertEqual(ret.result, 0)

        
    def testNonReservationHolderDoesNotHaveWriteAccess(self):
        """Non-Reservation Holders do not have write access to the WE target"""
        time.sleep(2)                   # give I/O time to sync up
        resvnA = initA.getReservation()
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        # initB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initB.dev,
                                "bs=512", "seek=1", "count=1"], Opts)
        self.assertEqual(ret.result, 1)
