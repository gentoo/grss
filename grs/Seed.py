#!/usr/bin/env python
#
#    Seed.py: this file is part of the GRS suite
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

import glob
import os
import re
import shutil
import urllib.request

from grs.Constants import CONST
from grs.Execute import Execute
from grs.Rotator import Rotator


class Seed(Rotator):
    """ Download a stage tarball and unpack it into an empty system portage configroot. """

    def __init__(self, stage_uri, tmpdir = CONST.TMPDIR, portage_configroot = \
            CONST.PORTAGE_CONFIGROOT, package = CONST.PACKAGE, logfile = CONST.LOGFILE):
        self.stage_uri = stage_uri
        self.portage_configroot = portage_configroot
        self.package = package
        filename = os.path.basename(stage_uri)
        self.filepath = os.path.join(tmpdir, filename)
        self.logfile = logfile


    def seed(self):
        # Rotate the old portage_configroot and package out of the way
        for directory in [self.portage_configroot, self.package]:
            self.full_rotate(directory)
            os.makedirs(directory, mode=0o755, exist_ok=False)

        # Download a stage tarball if we don't have one
        if not os.path.isfile(self.filepath):
            request = urllib.request.urlopen(self.stage_uri)
            with open(self.filepath, 'wb') as f:
                shutil.copyfileobj(request, f)

        # Because python's tarfile sucks
        cmd = 'tar --xattrs -xf %s -C %s' % (self.filepath, self.portage_configroot)
        Execute(cmd, timeout=120, logfile=self.logfile)
