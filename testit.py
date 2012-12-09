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

import unittest
import nose

if __name__ == '__main__':
    nose.main()
