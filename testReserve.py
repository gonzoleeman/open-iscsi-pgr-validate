#!/usr/bin/python
"""
Python tests for SCSI-3 Persistent Group Reservations

Description:
 This test suite verifies correct operation of a SCSI-3 PGR target
 over an iSCSI transport. It does this using coordinated access to
 that iSCSI target using multiple open-iscsi initiator interfaces.

 These tests are designed to be run sequentially and completely,
 i.e. you cannot skip tests, as the state of earlier tests is used
 when running later tests.

Requirements:
 - Abililty to run as root (for device access)
 - The sg3_utils package, specifically sg_persist (and sg_inq?)
 - The open-iscsi package, supporting "iface" files, and 2 (or 3) disk
   devices already configured, pointing to the same disc (using
   different iSCSI initiators) -- Will be automatic "some day"
 - An iSCSI target that claims to support Persistent Group
   Reservations


TODO
 - Add config file support
 - Add command-line option parsing
 - Better integrate with unittest and nose
 - Set up iSCSI iface targets instead of requiring that precondition
"""


__version__ = "Version 0.3"
__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


import sys
import os
import subprocess
import copy
import time

import unittest
import nose


#
# config stuff ...
#

my_debug = False
three_way = False

################################################################

class InitCfgItem:
    def __init__(self, iface_name, dev, key=None):
        self.iface_name = iface_name
        self.dev = dev
        self.key = key

initA = InitCfgItem("t1", "/dev/sdc", "0x123abc")
initB = InitCfgItem("t2", "/dev/sdd", "0x696969")
if three_way:
    initC = InitCfgItem("t3", "/dev/sde")

################################################################

# List of Reservation Types, for prout-type"""
ProutTypes = {
    "NoType" : "0",
    "WriteExclusive" : "1",
    "ExclusiveAccess" : "3",
    "WriteExclusiveRegistrantsOnly" : "5",
    "ExclusiveAccessRegistrantsOnly" : "6",
    "WriteExclusiveAllRegistrants" : "7",
    "ExclusiveAccessAllRegistrants" : "8"}

################################################################

def dprint(*args):
    """debug print"""
    if my_debug:
        print >>sys.stderr, 'DEBUG:',
        for arg in args:
            print >>sys.stderr, arg,
        print >>sys.stderr

class RunResult:
    def __init__(self, lines=None, result=None):
        self.lines = lines
        self.result = result
    
def runCmdWithOutput(cmd):
    """Run the supplied command array, returning array result"""
    dprint("Running command:", cmd)
    subproc = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    lines = []
    for line in subproc.stdout.xreadlines():
        dprint("Adding output=/%s/" % line.rstrip())
        lines.append(line.rstrip())
    xit_val = subproc.wait()
    if xit_val:
        dprint("Error: process returned:", xit_val)
        lines = None
    return RunResult(lines, xit_val)

def runSgCmdWithOutput(i, cmd):
    """Run the SG command on specified host"""
    my_cmd = ["sg_persist", "-n"] + cmd + [i.dev]
    return runCmdWithOutput(my_cmd)

def getRegistrants(i):
    """Get list of registrants remotely"""
    registrants = []
    res = runSgCmdWithOutput(i, ["-k"])
    if "no registered reservation keys" not in res.lines[0].lower():
        for l in res.lines[1:]:
            dprint("key=", l.strip())
            registrants.append(l.strip())
    dprint("returning registrants list=", registrants)
    return registrants

def register(i):
    """Register the remote I_T Nexus"""
    res = runSgCmdWithOutput(i, ["--out", "--register", "--param-sark=" + i.key])
    return res.result

def registerAndIgnore(i, new_key):
    """Register the remote I_T Nexus"""
    res = runSgCmdWithOutput(i,
                             ["--out", "--register",
                              "--param-rk=" + i.key,
                              "--param-sark=" + new_key])
    return res.result

def unregister(i):
    """UnRegister the remote I_T Nexus"""
    res = runSgCmdWithOutput(i,
                             ["--out", "--register",
                              "--param-rk=" + i.key])
    return res.result

def reserve(i, prout_type):
    """Reserve for the host using the supplied type"""
    res = runSgCmdWithOutput(i,
                             ["--out", "--reserve",
                              "--param-rk=" + i.key,
                              "--prout-type=" + prout_type])
    return res.result

def clear(i):
    """Clear Registrations and Reservation on a target"""
    res = runSgCmdWithOutput(i,
                             ["--out", "--clear",
                              "--param-rk=" + i.key])
    return res.result


class Reservation:
    def __init__(self, key=None, rtype=None):
        self.key = key
        self.rtype = rtype
    def getRtypeNum(self):
        ret = ProutTypes["NoType"]
        if self.rtype == "Exclusive Access":
            ret = ProutTypes["ExclusiveAccess"]
        elif self.rtype == "Write Exclusive":
            ret = ProutTypes["WriteExclusive"]
        dprint("Given rtype=%s, returning Num=%s" % (self.rtype,
                                                     ret))
        return ret

def getReservation(i):
    """Get current reservation"""
    res = runSgCmdWithOutput(i, ["-r"])
    dprint("Parsing %d lines of reservations:" % len(res.lines))
    for o in res.lines:
        dprint("line=", o)
    rr = Reservation()
    if "Reservation follows" in res.lines[0]:
        rr.key = res.lines[1].split("=")[1]
        pcs = res.lines[2].split(",")
        rr.rtype = pcs[1].split(":")[1].strip()
        dprint("Reservation: found key=", rr.key, "type=", rr.rtype)
    else:
        dprint("No Reservation found")
    return rr

def release(i, prout_type):
    """Reserve for the host using the supplied type"""
    res = runSgCmdWithOutput(i,
                             ["--out", "--release",
                              "--param-rk=" + i.key,
                              "--prout-type=" + prout_type])
    return res.result

################################################################

def verifyCmdExists(cmd):
    """Verify that the command exists"""
    dprint("Verifying command exists:", cmd)
    try:
        runCmdWithOutput(cmd)
    except Exception, e:
        print >>sys.stderr, "Fatal: Command not found: %s\n" % cmd[0]
        sys.exit(1)

def getDiskInquirySn(dev):
    """Get the Disk Serial Number"""
    res = runCmdWithOutput(["sg_inq", dev])
    ret = None
    if res.result == 0:
        if "Unit serial number" in res.lines[-1]:
            line = res.lines[-1]
            ret = line.split()[-1]
    dprint("getDiskInquirySn(%s) -> %s" % (dev, ret))
    return ret

def setUpModule():
    """Whole-module setup -- not yet used?"""
    dprint("Module-level setup ...")
    if os.geteuid() != 0:
        print >>sys.stderr, "Fatal: must be root to run this script\n"
        sys.exit(1)
    verifyCmdExists(["sg_persist", "-V"])
    verifyCmdExists(["sg_inq", "-V"])
    verifyCmdExists(["dd", "--version"])
    # make sure all devices are the same
    iiA = getDiskInquirySn(initA.dev)
    iiB = getDiskInquirySn(initB.dev)
    if not iiA or not iiB:
        print >>sys.stderr, "Fatal: cannot get INQUIRY data from %s or %s\n" % (initA.dev,
                                                                                initB.dev)
        sys.exit(1)
    if iiA != iiB:
        print >>sys.stderr, "Fatal: Serial numbers differ for %s and %s\n" % (initA.dev,
                                                                              initB.dev)
        sys.exit(1)
    if three_way:
        iiC = getDiskInquiryInfo(initC.dev)
        if not iiC:
            print >>sys.stderr, "Fatal: cannot get INQUIRY data from %s\n" % initC.dev
            sys.exit(1)


################################################################


class Test01CanRegisterTestCase(unittest.TestCase):
    """Can register initiators"""

    def setUp(self):
        """Set up for tests"""
        clear(initA)
        clear(initB)

    def testCanRegisterInitA(self):
        """Can register Initiator A"""
        resA = register(initA)
        self.assertEqual(resA, 0)

    def testCanRegisterInitB(self):
        """Can register Initiator B"""
        dprint("Registering host B ...")
        resB = register(initB)
        self.assertEqual(resB, 0)


################################################################

class Test02CanSeeRegistrationsTestCase(unittest.TestCase):
    """Can see initiator registration"""

    def setUp(self):
        """Set up for tests"""
        res = clear(initA)
        res = clear(initB)

    def testCanSeeNoRegistrations(self):
        """Can read and see no registrations when there are none"""
        registrantsA = getRegistrants(initA)
        self.assertEqual(len(registrantsA), 0)

    def testCanSeeRegistration(self):
        """Can see registration from same initiator"""
        res = register(initA)
        self.assertEqual(res, 0)
        res = register(initB)
        self.assertEqual(res, 0)
        registrantsA = getRegistrants(initA)
        self.assertEqual(len(registrantsA), 2)
        self.assertEqual(registrantsA[0], initA.key)
        self.assertEqual(registrantsA[1], initB.key)

    def testCanSeeRegOnDifferentInit(self):
        """Can see registration from another initiator"""
        resA = register(initA)
        self.assertEqual(resA, 0)
        registrantsB = getRegistrants(initB)
        self.assertEqual(len(registrantsB), 1)
        self.assertEqual(registrantsB[0], initA.key)

################################################################

class Test03CanUnregisterTestCase(unittest.TestCase):

    def setUp(self):
        """Set up for tests"""
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)

    def testCanUnregister(self):
        """Can unregister hosts"""
        res = unregister(initA)
        self.assertEqual(res, 0)
        registrants = getRegistrants(initA)
        self.assertEqual(len(registrants), 1)
        res = unregister(initB)
        self.assertEqual(res, 0)
        registrants = getRegistrants(initB)
        self.assertEqual(len(registrants), 0)


################################################################

class Test04ReregistrationFailsTestCase(unittest.TestCase):

    def setUp(self):
        """Set up for tests"""
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)

    def testReregisterFails(self):
        """Cannot re-register"""
        initAcopy = copy.copy(initA)
        initAcopy.key = "0x1"
        resA = register(initAcopy)
        self.assertNotEqual(resA, 0)
        registrantsA = getRegistrants(initA)
        self.assertEqual(len(registrantsA), 2)
        self.assertEqual(registrantsA[0], initA.key)
        self.assertEqual(registrantsA[1], initB.key)


################################################################

class Test05RegisterAndIgnoreTestCase(unittest.TestCase):

    def setUp(self):
        """Set up for tests"""
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)

    def test04CanRegisterAndIgnore(self):
        """Can register and ignore existing registrantion"""
        # register with key "0x1"
        initAcopy = copy.copy(initA)
        initAcopy.key = "0x1"
        result = registerAndIgnore(initA, initAcopy.key)
        self.assertEqual(result, 0)
        registrantsA = getRegistrants(initAcopy)
        self.assertEqual(registrantsA[0], initAcopy.key)
        # re-register with normal key
        result = registerAndIgnore(initAcopy, initA.key)
        self.assertEqual(result, 0)
        registrantsA = getRegistrants(initA)
        self.assertEqual(registrantsA[0], initA.key)


################################################################

class Test06CanReserveEaTestCase(unittest.TestCase):
    """Test that PGR RESERVE Exclusive Access works"""

    def setUp(self):
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)

    def testCanReserveEa(self):
        """Can reserve a target for exclusive access"""
        res = reserve(initA, ProutTypes["ExclusiveAccess"])
        self.assertEqual(res, 0)

################################################################

class Test07CanReadEaReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Exclusive Access can be read"""

    def setUp(self):
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)
        reserve(initA, ProutTypes["ExclusiveAccess"])

    def testCanReadReservationFromReserver(self):
        """Can read EA reservation from reserving host"""
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
 
    def testCanReadReservationFromNonReserver(self):
        """Can read EA reservation from non-reserving host"""
        resvnB = getReservation(initB)
        self.assertEqual(resvnB.key, initA.key)
        self.assertEqual(resvnB.getRtypeNum(), ProutTypes["ExclusiveAccess"])

    def testCanReadReservationFromNonRegistrant(self):
        """Can read EA reservation from non-registrant host"""
        if three_way:
            resvnC = getReservation(initC)
            self.assertEqual(resvnC.key, initA.key)
            self.assertEqual(resvnC.getRtypeNum(), ProutTypes["ExclusiveAccess"])


################################################################

class Test08CanReleseEaReservationTestCase(unittest.TestCase):
    """Test that PGR RESERVE Exclusive Access can be released"""

    def setUp(self):
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)
        reserve(initA, ProutTypes["ExclusiveAccess"])

    def test03CanReleaseReservation(self):
        """Can release an EA reservation from reserving host"""
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = release(initA, ProutTypes["ExclusiveAccess"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def test03CannotReleaseReservation(self):
        """Cannot release an EA reservation from non-reserving host"""
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = release(initB, ProutTypes["ExclusiveAccess"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])


################################################################

class Test09UnregisterEaHandlingTestCase(unittest.TestCase):
    """Test how PGR RESERVE Exclusive Access reservation is handled during unregistration"""

    def setUp(self):
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)
        reserve(initA, ProutTypes["ExclusiveAccess"])

    def test04UnregisterReleasesReservation(self):
        """Un-registration of reserving EA host releases reservation"""
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = unregister(initA)
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def test05UnregisterDoesNotReleaseReservation(self):
        """Un-registration of non-reserving EA host does not release reservation"""
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        res = unregister(initB)
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])

    def test06ReservationHolderHasAccess(self):
        """The Reservation Holder has Access to an EA target"""
        # initA get reservation
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        # initA read from disk to /dev/null
        time.sleep(2)                   # give I/O time to sync up
        ret = runCmdWithOutput(["dd", "if=" + initA.dev, "of=/dev/null",
                                "bs=512", "count=1"])
        self.assertEqual(ret.result, 0)
        # initA can write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initA.dev,
                                "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 0)
    
    def test07NonReservationHolderDoesNotHaveAccess(self):
        """Non-Reservation Holders do not have Access to an EA target"""
        # initA get reservation
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["ExclusiveAccess"])
        # initB can't read from disk to /dev/null
        time.sleep(2)                   # give I/O time to sync up
        ret = runCmdWithOutput(["dd", "if=" + initB.dev, "of=/dev/null",
                                "bs=512", "count=1"])
        self.assertEqual(ret.result, 1)
        # initB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initB.dev,
                                "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 1)
    

################################################################

class Test10ReserveWeTestCase(unittest.TestCase):
    """Test PGR RESERVE Write Exclusive"""

    def setUp(self):
        clear(initA)
        clear(initB)
        register(initA)
        register(initB)

    def test01CanReserve(self):
        """Can reserve a target for exclusive access"""
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)

    def test02CanReadReservation(self):
        """Can read WE reservation from all hosts"""
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        resvnB = getReservation(initB)
        self.assertEqual(resvnB.key, initA.key)
        self.assertEqual(resvnB.getRtypeNum(), ProutTypes["WriteExclusive"])
        if three_way:
            resvnC = getReservation(initC)
            self.assertEqual(resvnC.key, initA.key)
            self.assertEqual(resvnC.getRtypeNum(), ProutTypes["WriteExclusive"])

    def test03CanReleaseReservation(self):
        """Can release a WE reservation from reserving host"""
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = release(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def test03CannotReleaseReservation(self):
        """Cannot release a WE reservation from non-reserving host"""
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = release(initB, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])

    def test04UnregisterReleasesReservation(self):
        """Un-registration of reserving WE host releases reservation"""
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = unregister(initA)
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def test05UnregisterDoesNotReleaseReservation(self):
        """Un-registration of non-reserving WE host does not release reservation"""
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        res = unregister(initB)
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])

    def test06ReservationHolderHasAccess(self):
        """The Reservation Holder has Access to the WE target"""
        # initA get reservation
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        # initA read from disk to /dev/null
        time.sleep(2)                   # give I/O time to sync up
        ret = runCmdWithOutput(["dd", "if=" + initA.dev, "of=/dev/null",
                                "bs=512", "count=1"])
        self.assertEqual(ret.result, 0)
        # initA write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initA.dev,
                                "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 0)
    
    def test07NonReservationHolderDoesNotHaveAccess(self):
        """Non-Reservation Holders do not have Write Access to the WE target"""
        # initA get reservation
        res = reserve(initA, ProutTypes["WriteExclusive"])
        self.assertEqual(res, 0)
        resvnA = getReservation(initA)
        self.assertEqual(resvnA.key, initA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutTypes["WriteExclusive"])
        # initB can read from disk to /dev/null
        time.sleep(2)                   # give I/O time to sync up
        ret = runCmdWithOutput(["dd", "if=" + initB.dev, "of=/dev/null",
                                "bs=512", "count=1"])
        self.assertEqual(ret.result, 0)
        # initB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runCmdWithOutput(["dd", "if=/dev/zero", "of=" + initB.dev,
                                "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 1)
    


if __name__ == '__main__':
    nose.main()
