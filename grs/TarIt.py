#!/usr/bin/env python

import os
from datetime import datetime
from grs.Constants import CONST
from grs.Execute import Execute

class TarIt():

    def __init__(self, name, portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        self.portage_configroot = portage_configroot
        self.logfile = logfile

        year = str(datetime.now().year).zfill(4)
        month = str(datetime.now().month).zfill(2)
        day = str(datetime.now().day).zfill(2)
        self.tarball_name = '%s-%s%s%s.tar.xz' % (name, year, month, day)
        self.digest_name = '%s.DIGESTS' % self.tarball_name

    def tarit(self):
        cwd = os.getcwd()
        os.chdir(self.portage_configroot)
        tarball_path = os.path.join('..', self.tarball_name)
        xattr_opts = '--xattrs --xattrs-include=security.capability --xattrs-include=user.pax.flags'
        cmd = 'tar %s -Jcf %s .' % (xattr_opts, tarball_path)
        Execute(cmd, timeout=None, logfile=self.logfile)
        os.chdir(cwd)

    def hashit(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(self.portage_configroot, '..'))

        # Note: this first cmd clobbers the contents
        cmd = 'echo "# MD5 HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'md5sum %s' % self.tarball_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        cmd = 'echo "# SHA1 HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'sha1sum %s' % self.tarball_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        cmd = 'echo "# SHA512 HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'sha512sum %s' % self.tarball_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        cmd = 'echo "# WHIRLPOOL HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'whirlpooldeep %s' % self.tarball_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        os.chdir(cwd)
