#!/usr/bin/env python

import os
from copy import deepcopy
from grs.Constants import CONST
from grs.Execute import Execute

class MountDirectories():
    """ doc here
        more doc
    """

    def __init__(self, portage_configroot = CONST.PORTAGE_CONFIGROOT, package = CONST.PACKAGE, logfile = CONST.LOGFILE):
        """ doc here
            more doc
        """
        # The order is respected
        self.directories = [
            'dev',
            'dev/pts',
            { 'dev/shm' : ( 'tmpfs', 'shm' ) },
            'proc',
            'sys',
            'usr/portage',
            [ package, 'usr/portage/packages' ]
        ]
        # Once initiated, we'll only work with one portage_configroot
        self.portage_configroot = portage_configroot
        self.package = package
        self.logfile = logfile
        # We need to umount in the reverse order
        self.rev_directories = deepcopy(self.directories)
        self.rev_directories.reverse()

    def ismounted(self, mountpoint):
        # Obtain all the current mountpoints.  os.path.ismount() fails for for bind mounts,
        # so we obtain them all ourselves
        mountpoints = []
        for line in open('/proc/mounts', 'r').readlines():
            mountpoints.append(line.split()[1])
        # Let's make sure mountoint is canonical real path, no sym links,
        # since that's what /proc/mounts reports.
        mountpoint = os.path.realpath(mountpoint)
        return mountpoint in mountpoints

    def are_mounted(self):
        """ doc here
            more doc
        """
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
        """ doc here
            more doc
        """
        # If any our mounted, let's first unmount all, then mount all
        some_mounted, all_mounted = self.are_mounted()
        if some_mounted:
            self.umount_all()

        for mount in self.directories:
            if isinstance(mount, str):
                # Here source_directory is assumed to exist relative to /
                source_directory = mount
                target_directory = mount
            elif isinstance(mount, list):
                # Here source_directory is assumet to be an abspath
                # and we create it if it doesn't exist
                source_directory = mount[0]
                if not os.path.isdir(source_directory):
                    os.makedirs(source_directory)
                target_directory = mount[1]
            elif isinstance(mount, dict):
                tmp = list(mount.values())
                tmp = tmp[0]
                vfstype = tmp[0]
                vfsname = tmp[1]
                tmp = list(mount.keys())
                target_directory = tmp[0]
            target_directory = os.path.join(self.portage_configroot, target_directory)
            if not os.path.isdir(target_directory):
                os.makedirs(target_directory)
            if isinstance(mount, str):
                cmd = 'mount --bind /%s %s' % (source_directory, target_directory)
            elif isinstance(mount, list):
                cmd = 'mount --bind %s %s' % (source_directory, target_directory)
            elif isinstance(mount, dict):
                cmd = 'mount -t %s %s %s' % (vfstype, vfsname, target_directory)
            Execute(cmd, timeout=60, logfile=self.logfile)


    def umount_all(self):
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
