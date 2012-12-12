#!/usr/bin/python
"""
Module setup help
"""

__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


import os
import sys
from cmd import verifyCmdExists



################################################################

def set_up_module(ia, ib, ic):
    """Whole-module setup"""
    if os.geteuid() != 0:
        print >>sys.stderr, "Fatal: must be root to run this script\n"
        sys.exit(1)
    verifyCmdExists(["sg_persist", "-V"])
    verifyCmdExists(["sg_inq", "-V"])
    verifyCmdExists(["dd", "--version"])
    # make sure all devices are the same
    iiA = ia.getDiskInquirySn()
    iiB = ib.getDiskInquirySn()
    iiC = ic.getDiskInquirySn()
    if not iiA or not iiB or not iiC:
        print >>sys.stderr, \
              "Fatal: cannot get INQUIRY data from %s, %s, or %s\n" % \
              (ia.dev, ib.dev, ic.dev)
        sys.exit(1)
    if iiA != iiB or iiA != iiC:
        print >>sys.stderr, \
              "Fatal: Serial numbers differ for %s, %s, or %s\n" % \
              (ia.dev, ib.dev, ic.dev)
        sys.exit(1)

