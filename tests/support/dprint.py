#!/usr/bin/python
"""
Debug print subroutine
"""

import sys
import os

errh = sys.stderr
lfile = os.getenv("TR_LOGFILE")
if lfile:
    lh = open(lfile, "w")
    if lfile:
        errh = lh

def dprint(opts, *args):
    """debug print"""
    if opts.debug:
        print >>errh, 'DEBUG:',
        for arg in args:
            print >>errh, arg,
        print >>errh

