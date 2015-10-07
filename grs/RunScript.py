#!/usr/bin/env python
#
#    RunScript.py: this file is part of the GRS suite
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
import shutil
from grs.Constants import CONST
from grs.Execute import Execute

class RunScript():
    """ Run a script within the chroot. """

    def __init__(
            self, libdir=CONST.LIBDIR, portage_configroot=CONST.PORTAGE_CONFIGROOT,
            logfile=CONST.LOGFILE
    ):
        self.libdir = libdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile

    def runscript(self, script_name):
        # Copy the script form the GRS repo to the system's portage configroot's /tmp.
        # Don't add a suffix to the script since we will admit bash, python, etc.
        script_org = os.path.join(self.libdir, 'scripts/%s' % script_name)
        script_dst = os.path.join(self.portage_configroot, 'tmp/script')
        shutil.copy(script_org, script_dst)
        # Mark the script as excutable and execute it.
        os.chmod(script_dst, 0o0755)
        cmd = 'chroot %s /tmp/script' % self.portage_configroot
        Execute(cmd, timeout=None, logfile=self.logfile)
        # In the case of a clean script, it can delete itself, so
        # check if the script exists before trying to delete it.
        if os.path.isfile(script_dst):
            os.unlink(script_dst)
