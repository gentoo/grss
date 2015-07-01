#!/usr/bin/env python

import glob
import os
import re
import shutil
import urllib.request
from grs.Constants import CONST
from grs.Execute import Execute


class Seed():
    """ doc here
        more doc
    """

    def __init__(self, stage_uri, tmpdir = CONST.TMPDIR, portage_configroot = \
            CONST.PORTAGE_CONFIGROOT, package = CONST.PACKAGE, logfile = CONST.LOGFILE):
        """ doc here
            more doc
        """
        self.stage_uri = stage_uri
        self.portage_configroot = portage_configroot
        self.package = package
        filename = os.path.basename(stage_uri)
        self.filepath = os.path.join(tmpdir, filename)
        self.logfile = logfile


    def seed(self):
        """ doc here
            more doc
        """
        for directory in [self.portage_configroot, self.package]:
            # Rotate any previous directories out of the way
            dirs = glob.glob('%s.*' % directory)
            indexed_dir = {}
            for d in dirs:
                m = re.search('^.+\.(\d+)$', d)
                indexed_dir[int(m.group(1))] = d
            count = list(indexed_dir.keys())
            count.sort()
            count.reverse()
            for c in count:
                current_dir = indexed_dir[c]
                m = re.search('^(.+)\.\d+$', current_dir)
                next_dir = '%s.%d' % (m.group(1), c+1)
                shutil.move(current_dir, next_dir)
            # If there is a directory, then move it to %s.0
            if os.path.isdir(directory):
                shutil.move(directory, '%s.0' % directory)
            # Now that all prevous directory are out of the way,
            # create a new empty directory.  Fail if the directory
            # is still around.
            os.makedirs(directory, mode=0o755, exist_ok=False)

        # Download a stage tarball if we don't have one
        if not os.path.isfile(self.filepath):
            try:
                request = urllib.request.urlopen(self.stage_uri)
                with open(self.filepath, 'wb') as f:
                    shutil.copyfileobj(request, f)
            except: #any exception will do here
                pid = os.getpid()
                with open(self.logfile, 'r') as f:
                    f.write('SENDING SIGTERM to pid = %d\n' % pid)
                    f.close()
                os.kill(pid, signal.SIGTERM)

        # Because python's tarfile sucks
        cmd = 'tar --xattrs -xf %s -C %s' % (self.filepath, self.portage_configroot)
        Execute(cmd, timeout=120, logfile=self.logfile)
        #os.unlink(self.filepath)
