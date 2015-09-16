#!/usr/bin/env python
#
#    Execute.py: this file is part of the GRS suite
#    Copyright (C) 2015  Anthony G. Basile
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import signal
import shlex
import subprocess
import sys
import time
from grs.Constants import CONST

class Execute():
    """ Execute a shell command """

    def __init__(self, cmd, timeout = 1, extra_env = {}, failok = False, shell = False \
        logfile = CONST.LOGFILE):
        """ Execute a shell command.

            cmd         - Simple string of the command to be execute as a
                          fork()-ed child.
            timeout     - The time in seconds to wait() on the child before
                          sending a SIGTERM.  timeout = None means wait indefinitely.
            extra_env   - Dictionary of extra environment variables for the fork()-ed
                          child.  Note that the child inherits all the env variables
                          of the grandparent shell in which grsrun/grsup was spawned.
            logfile     - A file to log output to.  If logfile = None, then we log
                          to sys.stdout.
        """
        def signalexit():
            pid = os.getpid()
            f.write('SENDING SIGTERM to pid = %d\n' % pid)
            f.close()
            try:
                for i in range(10):
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.2)
                while True:
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.2)
            except ProcessLookupError:
                pass

        if shell:
            args = cmd
        else:
            args = shlex.split(cmd)
        extra_env = dict(os.environ, **extra_env)

        if logfile:
            f = open(logfile, 'a')
            proc = subprocess.Popen(args, stdout=f, stderr=f, env=extra_env, shell=shell)
        else:
            f = sys.stderr
            proc = subprocess.Popen(args, env=extra_env, shell=shell)

        try:
            proc.wait(timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            proc.kill()
            timed_out = True

        if not timed_out:
            # rc = None if we had a timeout
            rc = proc.returncode
            if rc:
                f.write('EXIT CODE: %d\n' % rc)
                if not failok:
                    signalexit()

        if timed_out:
            f.write('TIMEOUT ERROR: %s\n' % cmd)
            if not failok:
                signalexit()

        # Only close a logfile, don't close sys.stderr!
        if logfile:
            f.close()
