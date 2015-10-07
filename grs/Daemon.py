#!/usr/bin/env python
#
#    Daemon.py: this file is part of the GRS suite
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

import atexit
import os
import sys

class Daemon:
    """ Adopted from Sander Marechal's "A simple unix/linux daemon in Python"
        See: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

        To use, inherit by a subclass which overrides run() and does all the
        work.  You start the daemon with

            d = MyDaemon(pidfile, foo='1', bar='2')  # Any **kwargs after pidfile
            d.start()   # to start the daemon

        All signal handling should be defined in a subfunction within run().

        Note: This isn't completely general daemon code as it doesn't close stdout/stderr.
        Rather these are redirected to /var/log/grs/grs-daemon-<pid>.err to capture any
        exceptions for debugging.
    """

    def __init__(self, pidfile, **kwargs):
        # Since this will be used as a super class, we'll accept any **kwargs
        # and insert them to our internal __dict__.
        self.pidfile = pidfile
        for k in kwargs:
            self.__dict__[k] = kwargs[k]


    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: %s\n' % err)
            sys.exit(1)

        os.chdir('/')
        os.setsid()
        os.umask(0o22)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed %s\n' % err)
            sys.exit(1)

        # Dup stdin to /dev/null, and stdout and stderr to grs-daemon-<pid>.err
        si = open(os.devnull, 'r')
        os.dup2(si.fileno(), sys.stdin.fileno())

        os.makedirs('/var/log/grs', mode=0o755, exist_ok=True)
        se = open('/var/log/grs/grs-daemon-%d.err' % os.getpid(), 'a+')

        sys.stdout.flush()
        os.dup2(se.fileno(), sys.stdout.fileno())
        sys.stderr.flush()
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Use atexit to remove the pidfile when we shutdown.
        # No matter where the exit is initiated, eg from Execute.py
        # we are sure that atexit() will run and delete the pidfile.
        atexit.register(self.delpid)
        with open(self.pidfile, 'w') as pf:
            pf.write('%d\n' % os.getpid())


    def delpid(self):
        os.remove(self.pidfile)


    def run(self):
        pass


    def start(self):
        # If there's a pidfile when we try to startup, then:
        # 1) If the pidfile is stale, remove it and startup as usual.
        # 2) If we're already running, then don't start a second instance.
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            if not os.path.exists('/proc/%d' % pid):
                sys.stderr.write('unlinking stale pid file %s\n' % self.pidfile)
                os.unlink(self.pidfile)
            else:
                sys.stderr.write('process running with pid = %d\n' % pid)
                return

        self.daemonize()
        self.run()
