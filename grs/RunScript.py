#!/usr/bin/env python

import os
import shutil
from grs.Constants import CONST
from grs.Execute import Execute

class RunScript():
    """ Run a script within the chroot. """

    def __init__(self, libdir = CONST.LIBDIR, portage_configroot = CONST.PORTAGE_CONFIGROOT, 
            logfile = CONST.LOGFILE):
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
