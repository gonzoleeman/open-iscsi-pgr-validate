#!/usr/bin/python
"""
Python tests for SCSI-3 Persistent Group Reservations

Description:
 This test suite verifies correct operation of a SCSI-3 PGR target. It
 does this using coordinated access to that SCSI target using three
 different hosts. The target transport does not matter for this test.

 These tests are designed to be run sequentially and completely,
 i.e. you cannot skip tests, as the state of earlier tests is used
 when running later tests.

Requirements:
 - Three separate hosts that connect to a common SCSI target, and a
   place from which to run the test, which can be one of the hosts or
   can be a separate system that can reach the three hosts used for
   testing.
 - Root ssh password-less access on all 3 hosts
 - The sg3_utils package on all three hosts


TODO
 - Add config file support
 - Auto-detect device path on each system
 - Actually verify systems are talking to the same/correct device
"""

__version__ = "Version 0.1"

import sys
import os
import subprocess
import copy
import unittest

#
# config stuff ...
#

debug = False
three_way = False

################################################################

class HostCfgItem:
    def __init__(self, hostname, key=None,
                 sg_cmd="sg_persist", dev="/dev/sdc"):
        self.hostname = hostname
        self.key = key
        self.cmd = sg_cmd
        self.dev = dev

# hosts A and B are group members, and C is not, so C will
# never need a key
hostA = HostCfgItem("localhost", "0x123abc")
hostB = HostCfgItem("linux-server", "0x696969")
hostC = HostCfgItem("linux-s2", dev="/dev/sdd")

################################################################

class ProutType:
    NoType = "0"
    WriteExclusive = "1"
    ExclusiveAccess = "3"
    WriteExclusiveRegistrantsOnly = "5"
    ExclusiveAccessRegistrantsOnly = "6"
    WriteExclusiveAllRegistrants = "7"
    ExclusiveAccessAllRegistrants = "8"

################################################################

def dprint(*args):
    """debug print"""
    if debug:
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

def runSgCmdWithOutput(h, cmd):
    """Run the SG command on specified host"""
    my_cmd = ["ssh", h.hostname, h.cmd, "-n"] + cmd + [h.dev]
    return runCmdWithOutput(my_cmd)

def runSshCmdWithOutput(h, cmd):
    """Run the command using ssh on the specified host"""
    my_cmd = ["ssh", h.hostname] + cmd
    return runCmdWithOutput(my_cmd)

def getRegistrants(h):
    """Get list of registrants remotely"""
    registrants = []
    res = runSgCmdWithOutput(h, ["-k"])
    dprint("Parsing %d lines of registrants ..." % len(res.lines))
    for o in res.lines:
        dprint("line=", o)
    if "no registered reservation keys" not in res.lines[0].lower():
        for l in res.lines[1:]:
            dprint("key=", l.strip())
            registrants.append(l.strip())
    dprint("returning registrants list=", registrants)
    return registrants

def Register(h):
    """Register the remote I_T Nexus"""
    res = runSgCmdWithOutput(h,
                             ["--out", "--register", "--param-sark=" + h.key])
    return res.result

def RegisterAndIgnore(h, new_key):
    """Register the remote I_T Nexus"""
    res = runSgCmdWithOutput(h,
                             ["--out", "--register",
                              "--param-rk=" + h.key,
                              "--param-sark=" + new_key])
    return res.result

def Unregister(h):
    """UnRegister the remote I_T Nexus"""
    res = runSgCmdWithOutput(h,
                             ["--out", "--register",
                              "--param-rk=" + h.key])
    return res.result

def Reserve(h, prout_type):
    """Reserve for the host using the supplied type"""
    res = runSgCmdWithOutput(h,
                             ["--out", "--reserve",
                              "--param-rk=" + h.key,
                              "--prout-type=" + prout_type])
    return res.result

class Reservation:
    def __init__(self, key=None, rtype=None):
        self.key = key
        self.rtype = rtype
    def getRtypeNum(self):
        ret = ProutType.NoType
        if self.rtype == "Exclusive Access":
            ret = ProutType.ExclusiveAccess
        elif self.rtype == "Write Exclusive":
            ret = ProutType.WriteExclusive
        dprint("Given rtype=%s, returning Num=%s" % (self.rtype,
                                                     ret))
        return ret

def getReservation(h):
    """Get current reservation"""
    res = runSgCmdWithOutput(h, ["-r"])
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

def Release(h, prout_type):
    """Reserve for the host using the supplied type"""
    res = runSgCmdWithOutput(h,
                             ["--out", "--release",
                              "--param-rk=" + h.key,
                              "--prout-type=" + prout_type])
    return res.result

################################################################

def setUp():
    """Whole-module setup -- not yet used?"""
    # make sure we are root
    # make sure the sg_persist command exists
    # make sure the remote host exists
    # make sure we can find and run (as root) the sg_persist
    #  command on all hosts
    # make sure the device is the same on all hosts
    dprint("Module-level setup ...")
    pass

class Test01RegisterTestCase(unittest.TestCase):
    """Test PGR REGISTER Commands"""

    def test00EnsureNoRegistrants(self):
        """Make sure there are no registrations"""
        # make sure there are no registrants
        registrants = getRegistrants(hostA)
        if len(registrants) > 0:
            self.fail("Must start with no registrants")

    def test01CanRegister(self):
        """Can register all Initiators"""
        dprint("Registering host A ...")
        resA = Register(hostA)
        self.assertEqual(resA, 0)
        dprint("Registering host A ...")
        resB = Register(hostB)
        self.assertEqual(resB, 0)

    def test02CanReadRegistrants(self):
        """Can read registrants from each host"""
        num_registrants = 2
        registrantsA = getRegistrants(hostA)
        self.assertEqual(len(registrantsA), num_registrants)
        self.assertEqual(registrantsA[0], hostA.key)
        registrantsB = getRegistrants(hostB)
        self.assertEqual(len(registrantsB), num_registrants)
        self.assertEqual(registrantsB[1], hostB.key)
        for i in range(num_registrants):
            self.assertEqual(registrantsA[i], registrantsB[i])
        if three_way:
            registrantsC = getRegistrants(hostC)
            self.assertEqual(len(registrantsC), num_registrants)
            for i in range(num_registrants):
                self.assertEqual(registrantsA[i], registrantsC[i])

    def test03ReregisterFails(self):
        """Cannot re-register"""
        hostAcopy = copy.copy(hostA)
        hostAcopy.key = "0x1"
        resA = Register(hostAcopy)
        self.assertNotEqual(resA, 0)

    def test04CanRegisterAndIgnore(self):
        """Can register and ignore existing registrantion"""
        # register with key "0x1"
        hostAcopy = copy.copy(hostA)
        hostAcopy.key = "0x1"
        result = RegisterAndIgnore(hostA, hostAcopy.key)
        self.assertEqual(result, 0)
        registrantsA = getRegistrants(hostAcopy)
        self.assertEqual(registrantsA[0], hostAcopy.key)
        # re-register with normal key
        result = RegisterAndIgnore(hostAcopy, hostA.key)
        self.assertEqual(result, 0)
        registrantsA = getRegistrants(hostA)
        self.assertEqual(registrantsA[0], hostA.key)

    def test05CanUnregister(self):
        """Can unregister hosts"""
        res = Unregister(hostA)
        self.assertEqual(res, 0)
        res = Unregister(hostB)
        self.assertEqual(res, 0)
        registrants = getRegistrants(hostA)
        self.assertEqual(len(registrants), 0)


class Test02ReserveEATestCase(unittest.TestCase):
    """Test PGR RESERVE Exclusive Access"""

    def setUp(self):
        Register(hostA)
        Register(hostB)

    def test01CanReserve(self):
        """Can reserve a target for exclusive access"""
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)

    def test02CanReadReservation(self):
        """Can read EA reservation from all hosts"""
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        resvnB = getReservation(hostB)
        self.assertEqual(resvnB.key, hostA.key)
        self.assertEqual(resvnB.getRtypeNum(), ProutType.ExclusiveAccess)
        if three_way:
            resvnC = getReservation(hostC)
            self.assertEqual(resvnC.key, hostA.key)
            self.assertEqual(resvnC.getRtypeNum(), ProutType.ExclusiveAccess)

    def test03CanReleaseReservation(self):
        """Can release an EA reservation from reserving host"""
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        res = Release(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def test03CannotReleaseReservation(self):
        """Cannot release an EA reservation from non-reserving host"""
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        res = Release(hostB, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)

    def test04UnregisterReleasesReservation(self):
        """Un-registration of reserving host releases reservation"""
        dprint("test04 ...")
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        res = Unregister(hostA)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def test05UnregisterDoesNotReleaseReservation(self):
        """Un-registration of non-reserving host does not release reservation"""
        dprint("test05 ...")
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        res = Unregister(hostB)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)

    def test06ReservationHolderHasAccess(self):
        """The Reservation Holder has Access to the target"""
        dprint("test06 ...")
        # hostA get reservation
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        # hostA read from disk to /dev/null
        ret = runSshCmdWithOutput(hostA,
                                   ["dd", "if=" + hostA.dev, "of=/dev/null",
                                    "bs=512", "count=1"])
        self.assertEqual(ret.result, 0)
        # hostA write from /dev/zero to 2nd 512-byte block on disc
        ret = runSshCmdWithOutput(hostA,
                                   ["dd", "if=/dev/zero", "of=" + hostA.dev,
                                    "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 0)
    
    def test07NonReservationHolderDoesNotHaveAccess(self):
        """Non-Reservation Holders do not have Access to the target"""
        dprint("test07 ...")
        # hostA get reservation
        res = Reserve(hostA, ProutType.ExclusiveAccess)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.ExclusiveAccess)
        # hostB can't read from disk to /dev/null
        ret = runSshCmdWithOutput(hostB,
                                   ["dd", "if=" + hostB.dev, "of=/dev/null",
                                    "bs=512", "count=1"])
        self.assertEqual(ret.result, 1)
        # hostB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runSshCmdWithOutput(hostB,
                                   ["dd", "if=/dev/zero", "of=" + hostB.dev,
                                    "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 1)
    
    def tearDown(self):
        dprint("Tearing down after a RESERVE test")
        res = Unregister(hostA)
        if res == 6:
            Unregister(hostA)
        res = Unregister(hostB)
        if res == 6:
            Unregister(hostB)

class Test03ReserveWETestCase(unittest.TestCase):
    """Test PGR RESERVE Write Exclusive"""

    def setUp(self):
        Register(hostA)
        Register(hostB)

    def test01CanReserve(self):
        """Can reserve a target for exclusive access"""
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)

    def test02CanReadReservation(self):
        """Can read WE reservation from all hosts"""
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        resvnB = getReservation(hostB)
        self.assertEqual(resvnB.key, hostA.key)
        self.assertEqual(resvnB.getRtypeNum(), ProutType.WriteExclusive)
        if three_way:
            resvnC = getReservation(hostC)
            self.assertEqual(resvnC.key, hostA.key)
            self.assertEqual(resvnC.getRtypeNum(), ProutType.WriteExclusive)

    def test03CanReleaseReservation(self):
        """Can release an WE reservation from reserving host"""
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        res = Release(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)
    
    def test03CannotReleaseReservation(self):
        """Cannot release an WE reservation from non-reserving host"""
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        res = Release(hostB, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)

    def test04UnregisterReleasesReservation(self):
        """Un-registration of reserving host releases reservation"""
        dprint("test04 ...")
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        res = Unregister(hostA)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, None)
        self.assertEqual(resvnA.rtype, None)

    def test05UnregisterDoesNotReleaseReservation(self):
        """Un-registration of non-reserving host does not release reservation"""
        dprint("test05 ...")
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        res = Unregister(hostB)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)

    def test06ReservationHolderHasAccess(self):
        """The Reservation Holder has Access to the target"""
        dprint("test06 ...")
        # hostA get reservation
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        # hostA read from disk to /dev/null
        ret = runSshCmdWithOutput(hostA,
                                   ["dd", "if=" + hostA.dev, "of=/dev/null",
                                    "bs=512", "count=1"])
        self.assertEqual(ret.result, 0)
        # hostA write from /dev/zero to 2nd 512-byte block on disc
        ret = runSshCmdWithOutput(hostA,
                                   ["dd", "if=/dev/zero", "of=" + hostA.dev,
                                    "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 0)
    
    def test07NonReservationHolderDoesNotHaveAccess(self):
        """Non-Reservation Holders do not have Write Access to the target"""
        dprint("test07 ...")
        # hostA get reservation
        res = Reserve(hostA, ProutType.WriteExclusive)
        self.assertEqual(res, 0)
        resvnA = getReservation(hostA)
        self.assertEqual(resvnA.key, hostA.key)
        self.assertEqual(resvnA.getRtypeNum(), ProutType.WriteExclusive)
        # hostB can read from disk to /dev/null
        ret = runSshCmdWithOutput(hostB,
                                   ["dd", "if=" + hostB.dev, "of=/dev/null",
                                    "bs=512", "count=1"])
        self.assertEqual(ret.result, 0)
        # hostB can't write from /dev/zero to 2nd 512-byte block on disc
        ret = runSshCmdWithOutput(hostB,
                                   ["dd", "if=/dev/zero", "of=" + hostB.dev,
                                    "bs=512", "skip=1", "count=1"])
        self.assertEqual(ret.result, 1)
    
    def tearDown(self):
        dprint("Tearing down after a RESERVE test")
        res = Unregister(hostA)
        if res == 6:
            Unregister(hostA)
        res = Unregister(hostB)
        if res == 6:
            Unregister(hostB)
