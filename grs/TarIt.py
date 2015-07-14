#!/usr/bin/env python

import os
from datetime import datetime
from grs.Constants import CONST
from grs.Execute import Execute

class TarIt():
    """ Create a tarball of the system and generate the hash values. """

    def __init__(self, name, portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        self.portage_configroot = portage_configroot
        self.logfile = logfile
        # Prepare a year, month and day for a tarball name timestamp.
        self.year = str(datetime.now().year).zfill(4)
        self.month = str(datetime.now().month).zfill(2)
        self.day = str(datetime.now().day).zfill(2)
        self.tarball_name = '%s-%s%s%s.tar.xz' % (name, self.year, self.month, self.day)
        self.digest_name = '%s.DIGESTS' % self.tarball_name


    def tarit(self, alt_name = None):
        # Create the tarball with the default name unless an alt_name is given.
        if alt_name:
            self.tarball_name = '%s-%s%s%s.tar.xz' % (alt_name, self.year, self.month, self.day)
            self.digest_name = '%s.DIGESTS' % self.tarball_name
        # We have to cd into the system's portage configroot and then out again.
        cwd = os.getcwd()
        os.chdir(self.portage_configroot)
        tarball_path = os.path.join('..', self.tarball_name)
        # TODO: This needs to be generalized for systems that don't support xattrs
        xattr_opts = '--xattrs --xattrs-include=security.capability --xattrs-include=user.pax.flags'
        cmd = 'tar %s -Jcf %s .' % (xattr_opts, tarball_path)
        Execute(cmd, timeout=None, logfile=self.logfile)
        os.chdir(cwd)


    def hashit(self):
        """ Generate various hash values.  We hijack the 'logfile' which will
            actually be the file containing the hashes.
        """
        # We need to be in the parent of the system's portage configroot because
        # that's where we created the above tarball.  This should be the workdir,
        # but its probably safer to be pedantic here.
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
