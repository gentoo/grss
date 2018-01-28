#!/usr/bin/env python
#
#    TarIt.py: this file is part of the GRS suite
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
from datetime import datetime
from grs.Constants import CONST
from grs.Execute import Execute
from grs.HashIt import HashIt

class TarIt(HashIt):
    """ Create a tarball of the system. """

    def __init__(
        self,
        name,
        portage_configroot=CONST.PORTAGE_CONFIGROOT,
        logfile=CONST.LOGFILE
    ):
        self.portage_configroot = portage_configroot
        self.logfile = logfile
        # Prepare a year, month and day for a tarball name timestamp.
        self.year = str(datetime.now().year).zfill(4)
        self.month = str(datetime.now().month).zfill(2)
        self.day = str(datetime.now().day).zfill(2)
        self.medium_name = '%s-%s%s%s.tar.xz' % (name, self.year, self.month, self.day)
        self.digest_name = '%s.DIGESTS' % self.medium_name


    def tarit(self, alt_name=None):
        # Create the tarball with the default name unless an alt_name is given.
        if alt_name:
            self.medium_name = '%s-%s%s%s.tar.xz' % (alt_name, self.year, self.month, self.day)
            self.digest_name = '%s.DIGESTS' % self.medium_name
        # We have to cd into the system's portage configroot and then out again.
        cwd = os.getcwd()
        os.chdir(self.portage_configroot)
        tarball_path = os.path.join('..', self.medium_name)
        # TODO: This needs to be generalized for systems that don't support xattrs
        xattr_opts = '--xattrs --xattrs-include=security.capability --xattrs-include=user.pax.flags'
        cmd = 'tar %s -Jcf %s .' % (xattr_opts, tarball_path)
        Execute(cmd, timeout=None, logfile=self.logfile)
        os.chdir(cwd)
