#!/usr/bin/env python

import os
import re
import shutil
from grs.Constants import CONST
from grs.Execute import Execute

class Populate():
    """ doc here
        more doc
    """

    def __init__(self, nameserver, libdir = CONST.LIBDIR, workdir = CONST.WORKDIR, portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        self.nameserver = nameserver
        self.libdir = libdir
        self.workdir = workdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile

        self.etc = os.path.join(self.portage_configroot, 'etc')
        self.resolv_conf = os.path.join(self.etc, 'resolv.conf')


    def populate(self, cycle = True):
        cmd = 'rsync -av --delete --exclude=\'.git*\' %s/core/ %s' % (self.libdir, self.workdir)
        Execute(cmd, timeout=60, logfile = self.logfile)

        # Select the cycle
        if cycle: self.select_cycle(cycle)

        # Copy from /tmp/grs-work to /tmp/system
        cmd = 'rsync -av %s/ %s' % (self.workdir, self.portage_configroot)
        Execute(cmd, timeout=60, logfile = self. logfile)

        # Add any extra files
        os.makedirs(self.etc, mode=0o755, exist_ok=True)
        with open(self.resolv_conf, 'w') as f:
            f.write('nameserver %s' % self.nameserver)


    def select_cycle(self, cycle):
        cycled_files = {}
        for dirpath, dirnames, filenames in os.walk(self.workdir):
            for f in filenames:
                m = re.search('^(.+)\.CYCLE\.(\d+)', f)
                if m:
                    filename = m.group(1)
                    cycle_no = int(m.group(2))
                    cycled_files.setdefault(cycle_no, [])
                    cycled_files[cycle_no].append([dirpath, filename])

        if type(cycle) is bool:
            cycle_no = max(cycled_files)
        else:
            cycle_no = cycle
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

    def clean_subdirs(self, dirpath):
        path = os.path.join(self.portage_configroot, dirpath)
        try:
            uid = os.stat(path).st_uid
            gid = os.stat(path).st_gid
            mode = os.stat(path).st_mode
            shutil.rmtree(path)
            os.mkdir(path)
            os.chown(path, uid, gid)
            os.chmod(path, mode)
        except FileNotFoundError:
            pass


    def clean(self):
        self.clean_subdirs('tmp')
        self.clean_subdirs('var/tmp')
        self.clean_subdirs('var/log')
        try:
            os.unlink(self.resolv_conf)
        except FileNotFoundError:
            pass
