#!/usr/bin/env python

import os
import re
import signal
import sys
from grs.Constants import CONST
from grs.Daemon import Daemon
from grs.Log import Log
from grs.Kernel import Kernel
from grs.MountDirectories import MountDirectories
from grs.PivotChroot import PivotChroot
from grs.Populate import Populate
from grs.RunScript import RunScript
from grs.Synchronize import Synchronize
from grs.Seed import Seed
from grs.TarIt import TarIt


class Interpret(Daemon):
    """ doc here
        more doc
    """

    def run(self):
        """ doc here
            more doc
        """

        def handler(signum, frame):
            """ On SIGTERM, propagate the signal to all processes in the cgroup/subcgroup
                except yourself.  If a process won't terminate nicely, then kill it.
                Finally unmount all the mounted filesystems.  Hopefully this will work
                since there should be no more open files on those filesystems.
            """
            mypid = os.getpid()
            while True:
                with open(os.path.join(self.subcgroupdir, 'tasks'), 'r') as f:
                    lines = f.readlines()
                    if len(lines) <= 1:
                        break
                    for p in lines:
                        pid = int(p.strip())
                        if mypid == pid:
                            continue
                        try:
                            os.kill(pid, signal.SIGTERM)
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            try:
                md.umount_all()
            except NameError:
                pass
            sys.exit(signum + 128)

        signal.signal(signal.SIGINT,  handler)
        signal.signal(signal.SIGTERM, handler)

        def smartlog(l, obj, has_obj = True):
            if (has_obj and not obj) or (not has_obj and obj):
                lo.log('Bad command: %s' % l)
                return True
            if self.mock_run:
                lo.log(l)
                return True
            return False

        def stampit(progress):
            open(progress, 'w').close()

        nameserver  = CONST.nameservers[self.run_number]
        repo_uri    = CONST.repo_uris[self.run_number]
        stage_uri   = CONST.stage_uris[self.run_number]

        name        = CONST.names[self.run_number]
        libdir      = CONST.libdirs[self.run_number]
        logfile     = CONST.logfiles[self.run_number]
        tmpdir      = CONST.tmpdirs[self.run_number]
        workdir     = CONST.workdirs[self.run_number]
        package     = CONST.packages[self.run_number]
        kernelroot  = CONST.kernelroots[self.run_number]
        portage_configroot = CONST.portage_configroots[self.run_number]

        lo = Log(logfile)
        sy = Synchronize(repo_uri, name, libdir, logfile)
        se = Seed(stage_uri, tmpdir, portage_configroot, package, logfile)
        md = MountDirectories(portage_configroot, package, logfile)
        po = Populate(nameserver, libdir, workdir, portage_configroot, logfile)
        ru = RunScript(libdir, portage_configroot, logfile)
        pc = PivotChroot(tmdpir, portage_configroot, logfile)
        ke = Kernel(libdir, portage_configroot, kernelroot, package, logfile)
        bi = TarIt(name, portage_configroot, logfile)

        os.makedirs(tmpdir, mode=0o755, exist_ok=True)

        lo.rotate_logs()
        md.umount_all()

        # Both sync() + seed() are not scripted steps.
        # sync() is done unconditionally for an update run.
        progress = os.path.join(tmpdir, '.completed_sync')
        if not os.path.exists(progress) or self.update_run:
            sy.sync()
            stampit(progress)

        # seed() is never done for an update run
        progress = os.path.join(tmpdir, '.completed_seed')
        if not os.path.exists(progress) and not self.update_run:
            se.seed()
            stampit(progress)

        build_script = os.path.join(libdir, 'build')
        with open(build_script, 'r') as s:
            line_number = 0
            for l in s.readlines():
                line_number += 1

                # Skip lines with initial # as comments
                m = re.search('^(#).*$', l)
                if m:
                    continue

                # For a release run, execute every line of the build script.
                # For an update run, exexute only lines with a leading +.
                ignore_stamp = False
                m = re.search('^(\+)(.*)$', l)
                if m:
                    # There is a leading +, so remove it and skip if doing an update run
                    ignore_stamp = self.update_run
                    l = m.group(2)
                else:
                    # There is no leading +, so skip if this is an update run
                    if self.update_run:
                        continue

                progress = os.path.join(tmpdir, '.completed_%02d' % line_number)
                if os.path.exists(progress) and not ignore_stamp:
                    continue

                try:
                    m = re.search('(\S+)\s+(\S+)', l)
                    verb = m.group(1)
                    obj  = m.group(2)
                except AttributeError:
                    verb = l.strip()
                    obj = None

                if verb == '':
                    stampit(progress)
                    continue
                if verb == 'log':
                    if smartlog(l, obj):
                        stampit(progress)
                        continue
                    if obj == 'stamp':
                        lo.log('='*80)
                    else:
                        lo.log(obj)
                elif verb == 'mount':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    md.mount_all()
                elif verb == 'unmount':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    md.umount_all()
                elif verb == 'populate':
                    if smartlog(l, obj):
                        stampit(progress)
                        continue
                    po.populate(cycle=int(obj))
                elif verb == 'runscript':
                    if smartlog(l, obj):
                        stampit(progress)
                        continue
                    ru.runscript(obj)
                elif verb == 'pivot':
                    if smartlog(l, obj):
                        stampit(progress)
                        continue
                    pc.pivot(obj, md)
                elif verb == 'clean':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    po.clean()
                elif verb == 'kernel':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    ke.kernel()
                elif verb == 'tarit':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    bi.tarit()
                elif verb == 'hashit':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    bi.hashit()
                else:
                    lo.log('Bad command: %s' % l)

                stampit(progress)
