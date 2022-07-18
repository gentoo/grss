#!/usr/bin/env python
#
#    MountDirectories.py: this file is part of the GRS suite
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
from copy import deepcopy
from grs.Constants import CONST
from grs.Execute import Execute

class MountDirectories():
    """ This controls the mounting/unmounting of directories under the system's
        portage configroot.
    """

    def __init__(self, portage_configroot=CONST.PORTAGE_CONFIGROOT, \
            package=CONST.PACKAGE, portage=CONST.PORTAGE, logfile=CONST.LOGFILE):
        # The order is respected.  Note that 'dev' needs to be mounted beore 'dev/pts'.
        self.directories = [
            'dev',
            'dev/pts',
            {'dev/shm' : ('tmpfs', 'shm')},
            'proc',
            'sys',
            [portage, 'var/db/repos/gentoo'],
            [package, 'var/cache/binpkgs']
        ]
        # Once initiated, we only work with one portage_configroot
        self.portage_configroot = portage_configroot
        self.package = package
        self.portage = portage
        self.logfile = logfile
        # We need to umount in the reverse order
        self.rev_directories = deepcopy(self.directories)
        self.rev_directories.reverse()


    def ismounted(self, mountpoint):
        """ Obtain all the current mountpoints.  Since python's os.path.ismount()
            fails for for bind mounts, we obtain these ourselves from /proc/mounts.
        """
        mountpoints = []
        for line in open('/proc/mounts', 'r').readlines():
            mountpoints.append(line.split()[1])
        # Let's make sure mountoint is canonical real path, no sym links, since that's
        # what /proc/mounts reports.  Otherwise we can get a false negative on matching.
        mountpoint = os.path.realpath(mountpoint)
        return mountpoint in mountpoints


    def are_mounted(self):
        """ Return whether some or all of the self.directories[] are mounted.  """
        some_mounted = False
        all_mounted = True
        for mount in self.directories:
            if isinstance(mount, str):
                target_directory = mount
            elif isinstance(mount, list):
                target_directory = mount[1]
            elif isinstance(mount, dict):
                tmp = list(mount.keys())
                target_directory = tmp[0]
            target_directory = os.path.join(self.portage_configroot, target_directory)
            if self.ismounted(target_directory):
                some_mounted = True
            else:
                all_mounted = False
        return some_mounted, all_mounted


    def mount_all(self):
        """ Mount all the self.directories[] under the system's portage configroot.  """
        # If any are mounted, let's first unmount all, then mount all
        some_mounted, all_mounted = self.are_mounted()
        if some_mounted:
            self.umount_all()
        # Now go through each of the self.directories[] to be mounted in order.
        for mount in self.directories:
            if isinstance(mount, str):
                # In this case, the source_directory is assumed to exist relative to /
                # and we will just bind mount it in the system's portage configroot.
                source_directory = mount
                target_directory = mount
            elif isinstance(mount, list):
                # In this case, the source_directory is assumed to be an abspath, and
                # we create it if it doesn't already exist.
                source_directory = mount[0]
                os.makedirs(source_directory, mode=0o755, exist_ok=True)
                target_directory = mount[1]
            elif isinstance(mount, dict):
                # In this case, we are given the mountpoint, type and name,
                # so we just go right ahead and mount -t type name mountpoint.
                # This is useful for tmpfs filesystems.
                tmp = list(mount.values())
                tmp = tmp[0]
                vfstype = tmp[0]
                vfsname = tmp[1]
                tmp = list(mount.keys())
                target_directory = tmp[0]
            # Let's make sure the target_directory exists.
            target_directory = os.path.join(self.portage_configroot, target_directory)
            os.makedirs(target_directory, mode=0o755, exist_ok=True)
            # Okay now we're ready to do the actual mounting.
            if isinstance(mount, str):
                cmd = 'mount --bind /%s %s' % (source_directory, target_directory)
            elif isinstance(mount, list):
                cmd = 'mount --bind %s %s' % (source_directory, target_directory)
            elif isinstance(mount, dict):
                cmd = 'mount -t %s %s %s' % (vfstype, vfsname, target_directory)
            Execute(cmd, timeout=60, logfile=self.logfile)


    def umount_all(self):
        """ Unmount all the self.directories[]. """
        # We must unmount in the opposite order that we mounted.
        for mount in self.rev_directories:
            if isinstance(mount, str):
                target_directory = mount
            elif isinstance(mount, list):
                target_directory = mount[1]
            elif isinstance(mount, dict):
                tmp = list(mount.keys())
                target_directory = tmp[0]
            target_directory = os.path.join(self.portage_configroot, target_directory)
            if self.ismounted(target_directory):
                cmd = 'umount --force %s' % target_directory
                Execute(cmd, timeout=60, logfile=self.logfile)
