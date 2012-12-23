#!/usr/bin/python
"""
reservation stuff for PGR testing
"""

import logging

from cmd import runCmdWithOutput

################################################################

log = logging.getLogger('nose.user')

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


class Reservation:
    """Represents a reservation on a target"""
    def __init__(self):
        self.key = None
        self.rtype = None
    def getRtypeNum(self):
        """Get the reservation type, as a number (as a string)"""
        ret = ProutTypes["NoType"]
        if self.rtype == "Exclusive Access":
            ret = ProutTypes["ExclusiveAccess"]
        elif self.rtype == "Write Exclusive":
            ret = ProutTypes["WriteExclusive"]
        elif self.rtype == "Exclusive Access, registrants only":
            ret = ProutTypes["ExclusiveAccessRegistrantsOnly"]
        elif self.rtype == "Write Exclusive, registrants only":
            ret = ProutTypes["WriteExclusiveRegistrantsOnly"]
        elif self.rtype == "Exclusive Access, all registrants":
            ret = ProutTypes["ExclusiveAccessAllRegistrants"]
        elif self.rtype == "Write Exclusive, all registrants":
            ret = ProutTypes["WriteExclusiveAllRegistrants"]
        log.debug("Given rtype=%s, returning Num=%s" % \
               (self.rtype, ret))
        return ret
