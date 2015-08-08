#!/usr/bin/python
#
#    test-daemon.py: this file is part of the GRS suite
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
import sys
sys.path.append(os.path.abspath('..'))

import signal
import time
from grs import Daemon, Execute

class MyDaemon(Daemon):
    def run(self):
        def handler(signum, frame):
            if signum == signal.SIGHUP:
                with open('/tmp/daemon.hup', 'a') as f:
                    f.write('%s\n' % self.value)
            if signum == signal.SIGTERM:
                with open('/tmp/daemon.term', 'a') as f:
                    f.write('%s\n' % self.value)
                sys.exit(0)
        signal.signal(signal.SIGHUP,  handler)
        signal.signal(signal.SIGTERM, handler)
        while True: time.sleep(1)

if __name__ == "__main__":
    mypid1 = '/tmp/daemon1.pid'
    mypid2 = '/tmp/daemon2.pid'

    daemon1 = MyDaemon(mypid1, value='test1')
    daemon2 = MyDaemon(mypid2, value='test2')

    cgroupdir      = '/sys/fs/cgroup'
    grs_cgroup     = 'grs'
    grs_cgroupdir  = os.path.join(cgroupdir, grs_cgroup)

    os.makedirs(grs_cgroupdir, mode=0o755, exist_ok=True)
    if not os.path.ismount(grs_cgroupdir):
        cmd = 'mount -t cgroup -o none,name=grs grs %s' % grs_cgroupdir
        Execute(cmd)

    subcgroup    = 'test-daemon'
    subcgroupdir = os.path.join(grs_cgroupdir, subcgroup)
    os.makedirs(subcgroupdir, exist_ok=True)

    cmd = 'cgclassify -g name=%s:/%s %d' % (grs_cgroup, subcgroup, os.getpid())
    Execute(cmd)

    if len(sys.argv) != 2:
        print('%s [start1 start2 start12 pids killall]' % sys.argv[0])
        sys.exit(1)

    if 'start1' == sys.argv[1]:
        daemon1.start()
    elif 'start2' == sys.argv[1]:
        daemon2.start()
    elif 'start12' == sys.argv[1]:
        if not os.fork():
            daemon1.start()
        elif not os.fork():
            daemon2.start()
    elif 'pids' == sys.argv[1]:
        try:
            print('daemon1:\n%s' % open(mypid1, 'r').read())
        except FileNotFoundError:
            pass
        try:
            print('daemon2:\n%s' % open(mypid2, 'r').read())
        except FileNotFoundError:
            pass
        try:
            print('cgroup:\n%s' % open(os.path.join(subcgroupdir, 'tasks'), 'r').read())
        except FileNotFoundError:
            pass
    elif 'killall' == sys.argv[1]:
        with open(os.path.join(subcgroupdir, 'tasks'), 'r') as f:
            for p in f.readlines():
                pd = int(p.strip())
                if pd == os.getpid():
                    continue
                os.kill(pd, signal.SIGTERM)
    else:
        print("Unknown command")
        sys.exit(2)
