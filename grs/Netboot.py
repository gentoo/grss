#!/usr/bin/env python
#
#    Netboot.py: this file is part of the GRS suite
#    Copyright (C) 2017  Anthony G. Basile
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
from datetime import datetime
from grs.Constants import CONST
from grs.Execute import Execute
from grs.HashIt import HashIt

class Netboot(HashIt):
    """ Create a Netboot image of the system. """

    def __init__(
            self,
            name,
            libdir=CONST.LIBDIR,
            tmpdir=CONST.TMPDIR,
            portage_configroot=CONST.PORTAGE_CONFIGROOT,
            kernelroot=CONST.KERNELROOT,
            logfile=CONST.LOGFILE
    ):
        self.libdir = libdir
        self.tmpdir = tmpdir
        self.portage_configroot = portage_configroot
        self.kernelroot = kernelroot
        self.logfile = logfile
        # Prepare a year, month and day for a name timestamp.
        self.year = str(datetime.now().year).zfill(4)
        self.month = str(datetime.now().month).zfill(2)
        self.day = str(datetime.now().day).zfill(2)
        self.medium_name = 'initramfs-%s-%s%s%s' % (name, self.year, self.month, self.day)
        self.digest_name = '%s.DIGESTS' % self.medium_name
        self.kernelname = 'kernel-%s-%s%s%s' % (name, self.year, self.month, self.day)


    def netbootit(self, alt_name=None):
        """ TODO """
        if alt_name:
            self.medium_name = 'initramfs-%s-%s%s%s' % (alt_name, self.year, self.month, self.day)
            self.digest_name = '%s.DIGESTS' % self.medium_name

        # 1. Copy the kernel to the tmpdir directory.
        kernel_src = os.path.join(self.portage_configroot, 'boot/kernel')
        kernel_dst = os.path.join(self.tmpdir, self.kernelname)
        shutil.copy(kernel_src, kernel_dst)

        # 2. Unpack the initramfs into kernelroot/initramfs direcotry
        initramfs_root = os.path.join(self.kernelroot, 'initramfs')
        shutil.rmtree(initramfs_root, ignore_errors=True)
        os.makedirs(initramfs_root, mode=0o755, exist_ok=False)

        # We will only use xz compression
        initramfs_src = os.path.join(self.portage_configroot, 'boot/initramfs')
        cmd = 'xz -dc %s | cpio -idv' % (initramfs_src)

        cwd = os.getcwd()
        os.chdir(initramfs_root)
        Execute(cmd, timeout=600, logfile=self.logfile, shell=True)
        os.chdir(cwd)

        ''' The issue here was that busybox was build in the host env like the
        kernel and that means that we are using the host's ARCH and the cpuflags
        which are now poluting the initramfs.  The better approach to building
        a kernel and initramfs is to drop the Kernel.py module altogether and
        emerge genkernel in the fledgeling system via the script directive, set
        genkernel.conf via the populate directive and then just run genkernel.

        # 2.5 Don't trust genkernel's busybox, but copy in our own version
        # built in the system chroot.  This ensures it will work on the
        # target system.
        # TODO: We need to make sure that we've linked busybox staticly.
        busybox_src = os.path.join(self.portage_configroot, 'bin/busybox')
        busybox_dst = os.path.join(self.kernelroot, 'initramfs/bin/busybox')
        shutil.copy(busybox_src, busybox_dst)
        '''

        # 3. Make the squashfs image in the tmpdir directory.
        squashfs_dir = os.path.join(initramfs_root, 'mnt/cdrom')
        shutil.rmtree(squashfs_dir, ignore_errors=True)
        os.makedirs(squashfs_dir, mode=0o755, exist_ok=False)
        squashfs_path = os.path.join(squashfs_dir, 'image.squashfs')
        cmd = 'mksquashfs %s %s -xattrs -comp xz' % (self.portage_configroot, squashfs_path)
        Execute(cmd, timeout=None, logfile=self.logfile)

        # 4. Copy in the init script
        init_src = os.path.join(self.libdir, 'scripts/init')
        init_dst = os.path.join(initramfs_root, 'init')
        shutil.copy(init_src, init_dst)
        os.chmod(init_dst, 0o0755)

        # 5. Repack
        initramfs_dst = os.path.join(self.tmpdir, self.medium_name)
        cmd = 'find . -print | cpio -H newc -o | xz -9e --check=none -z -f > %s' % initramfs_dst

        cwd = os.getcwd()
        os.chdir(initramfs_root)
        Execute(cmd, timeout=600, logfile=self.logfile, shell=True)
        os.chdir(cwd)
