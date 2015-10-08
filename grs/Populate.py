#!/usr/bin/env python
#
#    Populate.py: this file is part of the GRS suite
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
from grs.Constants import CONST
from grs.Execute import Execute

class Populate():
    """ Copy the core files from the GRS repo to the system's portage configroot
        for a particular cycle number.
    """

    def __init__(
            self, libdir=CONST.LIBDIR, workdir=CONST.WORKDIR,
            portage_configroot=CONST.PORTAGE_CONFIGROOT, logfile=CONST.LOGFILE
    ):
        self.libdir = libdir
        self.workdir = workdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile


    def populate(self, cycle=True):
        """ Copy the core files from the GRS repo, to a local workdir and
            then to the system's portage configroot, selecting for a paricular
            cycle number.
        """
        # rsync from the GRS repo to the workdir, removing the .git directory
        cmd = 'rsync -av --delete --exclude=\'.git*\' %s/core/ %s' % (self.libdir, self.workdir)
        Execute(cmd, timeout=60, logfile=self.logfile)

        # Select the cycle
        if cycle:
            self.select_cycle(cycle)

        # Copy from the workdir to the system's portage configroot.
        cmd = 'rsync -av %s/ %s' % (self.workdir, self.portage_configroot)
        Execute(cmd, timeout=60, logfile=self.logfile)


    def select_cycle(self, cycle):
        """ Select files with the matching cycle number.  If a file has form
                filename.CYCLE.d
            where d is an integer, then we delete all the other filename.CYCLE.x
            where x != d and we rename filename.CYCLE.d to just filename.
            Note: if a cycle number is not given, then cycle default to True
            and we choose the filename with the largest cycle number.
        """
        # The cycled_files dictionary will have form:
        # { 1:['/path/to', 'a'], 1:['/path/to', 'b'], 2:...}
        cycled_files = {}
        for dirpath, dirnames, filenames in os.walk(self.workdir):
            for _file in filenames:
                _match = re.search(r'^(.+)\.CYCLE\.(\d+)', _file)
                if _match:
                    filename = _match.group(1)
                    cycle_no = int(_match.group(2))
                    cycled_files.setdefault(cycle_no, [])
                    cycled_files[cycle_no].append([dirpath, filename])
        # If cycle is just a boolean, then default to the maximum cycle number.
        if isinstance(cycle, bool):
            cycle_no = max(cycled_files)
        else:
            cycle_no = cycle
        # Go through cycled_files dictionary and either
        #     1. rename the file if it matches the desired cycle number,
        #     2. delete the file otherwise.
        for _cycle in cycled_files:
            for _file in cycled_files[_cycle]:
                dirpath = _file[0]
                filename = _file[1]
                new_file = os.path.join(dirpath, filename)
                old_file = "%s.CYCLE.%d" % (new_file, _cycle)
                if os.path.isfile(old_file):
                    if _cycle == cycle_no:
                        os.rename(old_file, new_file)
                    else:
                        os.remove(old_file)
