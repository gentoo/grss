#!/usr/bin/env python

import atexit
import os
import signal
import sys
import time

class Daemon:
    """ Adopted from Sander Marechal's "A simple unix/linux daemon in Python"
        See: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

        To use, inherit by a subclass which overrides run() and does all the
        daemon work.  You start the daemon with

            d = MyDaemon(pidfile, foo='1', bar='2')  # Any number for kwargs after pidfile
            d.start()   # to start the daemon
            d.restart() # to restart the daemon
            d.stop()    # to stop the daemon

        Note: This isn't completely general daemon code as it doesn't close stdout/stderr.
        Rather these are redirected to /var/log/grs/grs-daemon-<pid>.err to capture any
        exceptions for debugging.
    """

    def __init__(self, pidfile, **kwargs):
        """ Since this will be used as a super class, we'll accept any **kwargs
            and insert them to our internal __dict__.
        """
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
        with open(self.pidfile,'w') as pf:
            pf.write('%d\n' % os.getpid())


    def delpid(self):
        os.remove(self.pidfile)


    def start(self):
        # If there's a pidfile when we try to startup, then either
        # its stale or we're already running.  If the pidfile is stale,
        # remove it and startup as usual.  If we're already running,
        # then don't start a second instance.
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


    def stop(self):
        # Try to open our pidfile and read our pid.  If you have a pid but
        # there is no process at that pid, then we're not running and all
        # we have to do is cleanup our stale pidfile.a  If we can't get a
        # pid from our pidfile, then we've lost the original process.  Either
        # it crashed or something else killed the pidfile.  We don't know.
        # Finally if have a valid pid, send it a bunch of SIGTERMS followed
        # by SIGKILLS just in case.
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid and not os.path.exists('/proc/%d' % pid):
            sys.stderr.write('process not running\n')
            sys.stderr.write('unlinking stale pid file %s\n' % self.pidfile)
            os.unlink(self.pidfile)
            return

        if not pid:
            sys.stderr.write('process not running\n')
            return # not an error in a restart

        try:
            for i in range(10):
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)
            while True:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.2)
        except ProcessLookupError as err:
            try:
                os.remove(self.pidfile)
            except IOError as err:
                sys.stderr.write('%s\n' % err)
        except OSError as err:
            sys.stderr.write('%s\n' %err)
            return

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        pass
