#!/usr/bin/env python

import os
import signal
import shlex
import subprocess
from grs.Constants import CONST

class Execute():
    """ doc here
        more doc
    """

    def __init__(self, cmd, timeout = 1, extra_env = {}, failok = False, logfile = CONST.LOGFILE):
        """ doc here
            more doc
        """
        def signalexit():
            pid = os.getpid()
            f.write('SENDING SIGTERM to pid = %d\n' % pid)
            f.close()
            try:
                os.kill(pid, signal.SIGTERM)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        f = open(logfile, 'a')
        args = shlex.split(cmd)
        extra_env = dict(os.environ, **extra_env)

        proc = subprocess.Popen(args, stdout=f, stderr=f, env=extra_env)

        try:
            proc.wait(timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            proc.kill()
            timed_out = True

        rc = proc.returncode
        if rc != 0:
            f.write('EXIT CODE: %d\n' % rc)
            if not failok:
                signalexit()

        if timed_out:
            f.write('TIMEOUT ERROR:  %s\n' % cmd)

        f.close()
