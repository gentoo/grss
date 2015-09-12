#!/usr/bin/env python
#
#    HashIt.py: this file is part of the GRS suite
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
from grs.Execute import Execute

class HashIt():
    """ Create a DIGEST file for certain tarballs, or ISOs.  This class must
        be inherited by a class which sets the medium_name and digest_name,
        else we'll get an AttributeError exception.
    """

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
        cmd = 'md5sum %s' % self.medium_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        cmd = 'echo "# SHA1 HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'sha1sum %s' % self.medium_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        cmd = 'echo "# SHA512 HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'sha512sum %s' % self.medium_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        cmd = 'echo "# WHIRLPOOL HASH"'
        Execute(cmd, logfile=self.digest_name)
        cmd = 'whirlpooldeep %s' % self.medium_name
        Execute(cmd, timeout=60, logfile=self.digest_name)

        os.chdir(cwd)
