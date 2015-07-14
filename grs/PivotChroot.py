#!/usr/bin/env python

import glob
import re
import os
import shutil

from grs.Constants import CONST
from grs.MountDirectories import MountDirectories
from grs.Rotator import Rotator


class PivotChroot(Rotator):
    """ Move an inner chroot out to the new system portage configroot.  """

    def __init__(self, tmpdir = CONST.TMPDIR, portage_configroot = CONST.PORTAGE_CONFIGROOT, \
            logfile = CONST.LOGFILE):
        self.tmpdir = tmpdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile


    def pivot(self, subchroot, md):
        # If any directories are mounted, unmount them before pivoting.
        some_mounted, all_mounted = md.are_mounted()
        if some_mounted:
            md.umount_all()

        # Move the system's portage configroot out of the way to system.0,
        # then pivot the inner chroot to system.
        self.full_rotate(self.portage_configroot)
        inner_chroot = os.path.join('%s.0' % self.portage_configroot, subchroot)
        shutil.move(inner_chroot, os.path.join(self.tmpdir, 'system'))

        # Be conservative: only if all the directories were mounted on the old
        # system portage configroot to we remount on the newly pivoted root.
        if all_mounted:
            md.mount_all()
