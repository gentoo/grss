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
                with open(os.path.join(self.subcgroupdir, 'tasks'), 'r') as _file:
                    lines = _file.readlines()
                    if len(lines) <= 1:
                        break
                    for _pid in lines:
                        pid = int(_pid.strip())
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
                _md.umount_all()
            except NameError:
                pass
            sys.exit(signum + 128)


        def signalexit():
            pid = os.getpid()
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2.0)


        def semantic_action(_line, objs, n, execstr):
            """ Execute the directive """
            if self.mock_run:
                _lo.log(_line)
                return
            try:
                if len(objs) < n:
                    raise Exception('Number of objs for verb incorrect.')
                exec(execstr)
            except Exception as e:
                _lo.log('Bad command: %s' % _line)
                _lo.log('Exception throw: %s' % e)
                _lo.log('SENDING SIGTERM to pid = %d\n' % pid)
                signalexit()


        def stampit(progress):
            """ Create an empty file to mark the progress through the
                build script.
            """
            open(progress, 'w').close()


        # Register the signals to terminate the entire process cgroup
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

        # Grab all the GRS namespace variables
        repo_uri = CONST.repo_uris[self.run_number]
        stage_uri = CONST.stage_uris[self.run_number]
        name = CONST.names[self.run_number]
        libdir = CONST.libdirs[self.run_number]
        logfile = CONST.logfiles[self.run_number]
        tmpdir = CONST.tmpdirs[self.run_number]
        workdir = CONST.workdirs[self.run_number]
        package = CONST.packages[self.run_number]
        kernelroot = CONST.kernelroots[self.run_number]
        portage_configroot = CONST.portage_configroots[self.run_number]

        # Initialize all the classes that will run the directives from
        # the build script.  Note that we expect these classes to just
        # initialize some variables but not do any work in their initializers.
        _lo = Log(logfile)
        _sy = Synchronize(repo_uri, name, libdir, logfile)
        _se = Seed(stage_uri, tmpdir, portage_configroot, package, logfile)
        _md = MountDirectories(portage_configroot, package, logfile)
        _po = Populate(libdir, workdir, portage_configroot, logfile)
        _ru = RunScript(libdir, portage_configroot, logfile)
        _pc = PivotChroot(tmpdir, portage_configroot, logfile)
        _ke = Kernel(libdir, portage_configroot, kernelroot, package, logfile)
        _bi = TarIt(name, portage_configroot, logfile)
        _io = ISOIt(name, libdir, tmpdir, portage_configroot, logfile)

        # Just in case /var/tmp/grs doesn't already exist.
        os.makedirs(tmpdir, mode=0o755, exist_ok=True)

        # Rotate any prevously existing logs and make unmount any existing
        # bind mounts from a previous run that were not cleaned up.
        _lo.rotate_logs()
        _md.umount_all()

        # Both sync() + seed() do not need build script directives.
        # sync() is done unconditionally for an update run.
        progress = os.path.join(tmpdir, '.completed_sync')
        if not os.path.exists(progress) or self.update_run:
            _sy.sync()
            stampit(progress)

        # seed() is never done for an update run
        progress = os.path.join(tmpdir, '.completed_seed')
        if not os.path.exists(progress) and not self.update_run:
            _se.seed()
            stampit(progress)

        # Read the build script and execute a line at a time.
        build_script = os.path.join(libdir, 'build')
        with open(build_script, 'r') as _file:
            line_number = 0
            medium_type = None
            for _line in _file.readlines():
                # Increment the line number by one and create the name of the
                # file for the progress stamp.
                line_number += 1
                progress = os.path.join(tmpdir, '.completed_%02d' % line_number)

                # Do nothing for lines with initial # or blank lines.  Create
                # a progress stamp only if we are not doing an update run.
                if re.search(r'^(#).*$', _line) or _line.strip() == '' or _line.strip() == '+':
                    if not self.update_run:
                        stampit(progress)
                    continue

                # For a release run, execute every line of the build script.
                # For an update run, exexute only lines with a leading +.
                ignore_stamp = False
                _match = re.search(r'^(\+)(.*)$', _line)
                if _match:
                    # There is a leading +, so remove it and ignore any progress
                    # stamp if its an update run.
                    ignore_stamp = self.update_run
                    _line = _match.group(2)
                else:
                    # There is no leading +, so skip if this is an update run
                    if self.update_run:
                        continue

                # Skip a line if the progres stamp exists, or ignore it
                # because its an update run.
                if os.path.exists(progress) and not ignore_stamp:
                    continue

                # This is pretty simple syntax.  The first word on a line
                # is a verb.  The remaining words are objcts.
                sentence = _line.split()
                verb = sentence[0]
                objs = sentence[1:]

                # This long concatenated if is where the semantics of the
                # build script are implemented.  Note: 'hashit' can only come
                # after 'tarit' or 'isoit' so that it knows the medium_name
                # to hash, ie whether its a .tar.xz or a .iso
                if verb == 'log':
                    if objs[0] == 'stamp':
                        objs[0] = '='*80
                    semantic_action(_line, objs, 1, '_lo.log(\' \'.join(objs))')
                elif verb == 'mount':
                    semantic_action(_line, objs, 0, '_md.mount_all()')
                elif verb == 'unmount':
                    semantic_action(_line, objs, 0, '_md.umount_all()')
                elif verb == 'populate':
                    semantic_action(_line, objs, 1, '_po.populate(cycle=int(objs[0]))')
                elif verb == 'runscript':
                    semantic_action(_line, objs, 1, '_ru.runscript(objs[0])')
                elif verb == 'pivot':
                    semantic_action(_line, objs, 1, '_pc.pivot(objs[0], _md)')
                elif verb == 'kernel':
                    semantic_action(_line, objs, 0, '_ke.kernel()')
                elif verb == 'tarit':
                    # 'tarit' can either be just a verb, or a 'verb obj' pair.
                    if len(objs):
                        semantic_action(_line, objs, 1, '_bi.tarit(objs[0])')
                    else:
                        semantic_action(_line, objs, 0, '_bi.tarit()')
                    medium_type = 'tarit'
                elif verb == 'isoit':
                    # 'isoit' can either be just a verb, or a 'verb obj' pair.
                    if len(objs):
                        semantic_action(_line, objs, 1, '_io.isoit(objs[1])')
                    else:
                        semantic_action(_line, objs, 0, '_io.isoit()')
                    medium_type = 'isoit'
                elif verb == 'hashit':
                    if medium_type == 'tarit':
                        semantic_action(_line, objs, 0, '_bi.hashit()')
                    elif medium_type == 'isoit':
                        semantic_action(_line, objs, 0, '_io.hashit()')
                    else:
                        raise Exception('Unknown medium to hash.')
                else:
                    _lo.log('Bad command: %s' % _line)
                    _lo.log('Unknown verb: %s' % verb)
                    _lo.log('SENDING SIGTERM to pid = %d\n' % pid)
                    signalexit()

                stampit(progress)

        # Just in case the build script lacks a final unmount, if we
        # are done, then let's make sure we clean up after ourselves.
        try:
            _md.umount_all()
        except NameError:
            pass
