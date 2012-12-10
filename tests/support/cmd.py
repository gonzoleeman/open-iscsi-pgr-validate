#!/usr/bin/python
"""
cmd -- Command module for PGR testing
"""


import subprocess

from dprint import dprint


class RunResult:
    def __init__(self, lines=None, result=None):
        self.lines = lines
        self.result = result
    
def runCmdWithOutput(cmd, opts):
    """Run the supplied command array, returning array result"""
    dprint(opts, "Running command:", cmd)
    subproc = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    lines = []
    for line in subproc.stdout.xreadlines():
        dprint(opts, "Adding output=/%s/" % line.rstrip())
        lines.append(line.rstrip())
    xit_val = subproc.wait()
    if xit_val:
        dprint(opts, "Error: process returned:", xit_val)
        lines = None
    return RunResult(lines, xit_val)

def verifyCmdExists(cmd, opts):
    """Verify that the command exists"""
    dprint(opts, "Verifying command exists:", cmd)
    try:
        runCmdWithOutput(cmd, opts)
    except Exception, e:
        print >>sys.stderr, "Fatal: Command not found: %s\n" % cmd[0]
        sys.exit(1)
