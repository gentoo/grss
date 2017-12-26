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
        self.digest_name = 'initramfs-%s.DIGESTS' % self.medium_name


    def netbootit(self, alt_name=None):
        """ TODO """
        if alt_name:
            self.medium_name = 'initramfs-%s-%s%s%s' % (alt_name, self.year, self.month, self.day)
            self.digest_name = 'initramfs-%s.DIGESTS' % self.medium_name

        # 0. Pepare netboot directory
        netboot_dir = os.path.join(self.tmpdir, 'netboot')
        shutil.rmtree(netboot_dir, ignore_errors=True)
        os.makedirs(netboot_dir, mode=0o755, exist_ok=False)

        # 1. Move the kernel into the netboot directory.
        kernel_dir = os.path.join(self.portage_configroot, 'boot')
        kernel_path = os.path.join(kernel_dir, 'kernel')
        shutil.copy(kernel_path, netboot_dir)

        # 2. Unpack the initramfs into kernelroot/initramfs direcotry
        initramfs_root = os.path.join(self.kernelroot, 'initramfs')
        shutil.rmtree(initramfs_root, ignore_errors=True)
        os.makedirs(initramfs_root, mode=0o755, exist_ok=False)

        initramfs_path = os.path.join(kernel_dir, 'initramfs')
        cmd = 'xz -dc %s | cpio -idv' % (initramfs_path)

        cwd = os.getcwd()
        os.chdir(initramfs_root)
        Execute(cmd, timeout=600, logfile=self.logfile, shell=True)
        os.chdir(cwd)

        # 3. Make the squashfs image in the netboot directory.
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
        initramfs_path = os.path.join(netboot_dir, self.medium_name)
        cmd = 'find . -print | cpio -H newc -o | gzip -9 > %s' % initramfs_path

        cwd = os.getcwd()
        os.chdir(initramfs_root)
        Execute(cmd, timeout=600, logfile=self.logfile, shell=True)
        os.chdir(cwd)
