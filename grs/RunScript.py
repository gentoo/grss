#!/usr/bin/env python

import os
import shutil
from grs.Constants import CONST
from grs.Execute import Execute

class RunScript():
    """ doc here
        more doc
    """

    def __init__(self, libdir = CONST.LIBDIR, portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        """ doc here
            more doc
        """
        self.libdir = libdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile

    def runscript(self, script_name):
        script_org = os.path.join(self.libdir, 'scripts/%s' % script_name)
        script_dst = os.path.join(self.portage_configroot, 'tmp/script.sh')
        shutil.copy(script_org, script_dst)
        os.chmod(script_dst, 0o0755)
        cmd = 'chroot %s /tmp/script.sh' % self.portage_configroot
        Execute(cmd, timeout=None, logfile=self.logfile)
        os.unlink(script_dst)
