#!/usr/bin/env python
#
#    Interpret.py: this file is part of the GRS suite
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
import re
import signal
import sys
import time

from grs.Constants import CONST
from grs.Daemon import Daemon
from grs.ISOIt import ISOIt
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
    """ This is the main daemon class. """

    def run(self):
        """ This overrides the empty Daemon run method and is started when .start()
            is executed.  This first daemonizes the process and then runs this method.
            Note that the Daemon class does not set up any signal handles and expects
            that to be done in the subclass.
        """

        # First we set up some inner methods:
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
                            for i in range(10):
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(0.2)
                            while True:
                                os.kill(pid, signal.SIGKILL)
                                time.sleep(0.2)
                        except ProcessLookupError:
                            pass
            try:
                md.umount_all()
            except NameError:
                pass
            sys.exit(signum + 128)


        def smartlog(l, obj, has_obj = True):
            """ This logs whether or not we have a grammatically incorrect
                directive, or we are doing a mock run, and returns whether
                or not we should execute the directive:
                    True  = skip this directive
                    False = don't skip it
            """
            if (has_obj and not obj) or (not has_obj and obj):
                lo.log('Bad command: %s' % l)
                return True
            if self.mock_run:
                lo.log(l)
                return True
            return False


        def stampit(progress):
            """ Create an empty file to mark the progress through the
                build script.
            """
            open(progress, 'w').close()


        # Register the signals to terminate the entire process cgroup
        signal.signal(signal.SIGINT,  handler)
        signal.signal(signal.SIGTERM, handler)

        # Grab all the GRS namespace variables
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

        # Initialize all the classes that will run the directives from
        # the build script.  Note that we expect these classes to just
        # initialize some variables but not do any work in their initializers.
        lo = Log(logfile)
        sy = Synchronize(repo_uri, name, libdir, logfile)
        se = Seed(stage_uri, tmpdir, portage_configroot, package, logfile)
        md = MountDirectories(portage_configroot, package, logfile)
        po = Populate(libdir, workdir, portage_configroot, logfile)
        ru = RunScript(libdir, portage_configroot, logfile)
        pc = PivotChroot(tmpdir, portage_configroot, logfile)
        ke = Kernel(libdir, portage_configroot, kernelroot, package, logfile)
        bi = TarIt(name, portage_configroot, logfile)
        io = ISOIt(name, libdir, tmpdir, portage_configroot, logfile)

        # Just in case /var/tmp/grs doesn't already exist.
        os.makedirs(tmpdir, mode=0o755, exist_ok=True)

        # Rotate any prevously existing logs and make unmount any existing
        # bind mounts from a previous run that were not cleaned up.
        lo.rotate_logs()
        md.umount_all()

        # Both sync() + seed() do not need build script directives.
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

        # Read the build script and execute a line at a time.
        build_script = os.path.join(libdir, 'build')
        with open(build_script, 'r') as s:
            line_number = 0
            for l in s.readlines():
                line_number += 1

                # Skip lines with initial # as comments.
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

                # This is pretty simple interpretive logic, either its a
                # single 'verb', or a 'verb obj' pair.  While restrictive,
                # its good enough for now.
                try:
                    m = re.search('(\S+)\s+(\S+)', l)
                    verb = m.group(1)
                    obj  = m.group(2)
                except AttributeError:
                    verb = l.strip()
                    obj = None

                # This long concatenated if is where the semantics of the
                # build script are implemented.  Note: 'hashit' can only come
                # after 'tarit' or 'isoit' so that it knows the medium_name
                # to hash, ie whether its a .tar.xz or a .iso
                medium_type = None
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
                elif verb == 'kernel':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    ke.kernel()
                elif verb == 'tarit':
                    # 'tarit' can either be just a verb,
                    # or a 'verb obj' pair.
                    if obj:
                        smartlog(l, obj, True)
                        bi.tarit(obj)
                    else:
                        smartlog(l, obj, False)
                        bi.tarit()
                    medium_type = 'tarit'
                elif verb == 'isoit':
                    # 'isoit' can either be just a verb,
                    # or a 'verb obj' pair.
                    if obj:
                        smartlog(l, obj, True)
                        io.isoit(obj)
                    else:
                        smartlog(l, obj, False)
                        io.isoit()
                    medium_type = 'isoit'
                elif verb == 'hashit':
                    if smartlog(l, obj, False):
                        stampit(progress)
                        continue
                    if medium_type == 'tarit':
                        bi.hashit()
                    elif medium_type == 'isoit':
                        io.hashit()
                    else:
                        raise Exception('Unknown medium to hash.')
                else:
                    lo.log('Bad command: %s' % l)

                stampit(progress)

        # Just in case the build script lacks a final unmount, if we
        # are done, then let's make sure we clean up after ourselves.
        try:
            md.umount_all()
        except NameError:
            pass
