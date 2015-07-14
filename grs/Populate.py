#!/usr/bin/env python

import os
import re
import shutil
from grs.Constants import CONST
from grs.Execute import Execute

class Populate():
    """ Copy the core files from the GRS repo to the system's portage configroot
        for a particular cycle number.
    """

    def __init__(self, nameserver, libdir = CONST.LIBDIR, workdir = CONST.WORKDIR, \
            portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        self.nameserver = nameserver
        self.libdir = libdir
        self.workdir = workdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile
        # We need /etc and /etc/resolv.conf for the system's portage configroot.
        self.etc = os.path.join(self.portage_configroot, 'etc')
        self.resolv_conf = os.path.join(self.etc, 'resolv.conf')


    def populate(self, cycle = True):
        """ Copy the core files from the GRS repo, to a local workdir and
            then to the system's portage configroot, selecting for a paricular
            cycle number.
        """
        # rsync from the GRS repo to the workdir, removing the .git directory
        cmd = 'rsync -av --delete --exclude=\'.git*\' %s/core/ %s' % (self.libdir, self.workdir)
        Execute(cmd, timeout=60, logfile = self.logfile)

        # Select the cycle
        if cycle: self.select_cycle(cycle)

        # Copy from the workdir to the system's portage configroot.
        cmd = 'rsync -av %s/ %s' % (self.workdir, self.portage_configroot)
        Execute(cmd, timeout=60, logfile = self. logfile)

        # Add /etc/resolv.conf.  We need this when we emerge within the chroot.
        os.makedirs(self.etc, mode=0o755, exist_ok=True)
        with open(self.resolv_conf, 'w') as f:
            f.write('nameserver %s' % self.nameserver)


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
            for f in filenames:
                m = re.search('^(.+)\.CYCLE\.(\d+)', f)
                if m:
                    filename = m.group(1)
                    cycle_no = int(m.group(2))
                    cycled_files.setdefault(cycle_no, [])
                    cycled_files[cycle_no].append([dirpath, filename])
        # If cycle is just a boolean, then default to the maximum cycle number.
        if type(cycle) is bool:
            cycle_no = max(cycled_files)
        else:
            cycle_no = cycle
        # Go through cycled_files dictionary and either
        #     1. rename the file if it matches the desired cycle number,
        #     2. delete the file otherwise.
        for c in cycled_files:
            for f in cycled_files[c]:
                dirpath = f[0]
                filename = f[1]
                new_file = os.path.join(dirpath, filename)
                old_file = "%s.CYCLE.%d" % (new_file, c)
                if os.path.isfile(old_file):
                    if c == cycle_no:
                        os.rename(old_file, new_file)
                    else:
                        os.remove(old_file)
