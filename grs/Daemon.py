#!/usr/bin/env python

import atexit
import os
import signal
import sys
import time

class Daemon:
    """ doc here
        more doc
        Adopted from Sander Marechal's "A simple unix/linux daemon in Python"
        See: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
    """

    def __init__(self, pidfile, **kwargs):
        self.pidfile = pidfile
        for k in kwargs:
            self.__dict__[k] = kwargs[k]

    def daemonize(self):
        """ doc here
            more doc
        """

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

        atexit.register(self.delpid)
        with open(self.pidfile,'w') as pf:
            pf.write('%d\n' % os.getpid())


    def delpid(self):
        os.remove(self.pidfile)


    def start(self):
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
