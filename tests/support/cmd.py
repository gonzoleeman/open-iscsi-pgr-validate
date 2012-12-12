#!/usr/bin/python
"""
cmd -- Command module for PGR testing
"""


import subprocess
import logging


__author__ = "Lee Duncan <leeman.duncan@gmail.com>"

__all__ = [
    'RunResult',
    'runCmdWithOutput',
    'verifyCmdExists'
    ]

################################################################

log = logging.getLogger('nose.user')

################################################################

class RunResult:
    def __init__(self, lines=None, result=None):
        self.lines = lines
        self.result = result
    
def runCmdWithOutput(cmd):
    """Run the supplied command array, returning array result"""
    log.debug("Running command: %s" % cmd)
    subproc = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    lines = []
    for line in subproc.stdout.xreadlines():
        log.debug("Adding output=/%s/" % line.rstrip())
        lines.append(line.rstrip())
    xit_val = subproc.wait()
    if xit_val:
        log.debug("Error: process returned: %d" % xit_val)
        lines = None
    return RunResult(lines, xit_val)

def verifyCmdExists(cmd):
    """Verify that the command exists"""
    log.debug("Verifying command exists: %s" % cmd)
    try:
        runCmdWithOutput(cmd)
    except Exception, e:
        print >>sys.stderr, "Fatal: Command not found: %s\n" % cmd[0]
        sys.exit(1)
