#!/usr/bin/env python
#
#    ISOIt.py: this file is part of the GRS suite
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

class ISOIt(HashIt):
    """ Create a bootable ISO of the system. """

    def __init__(self, name, libdir = CONST.LIBDIR, workdir = CONST.WORKDIR, \
            portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        self.libdir = libdir
        self.workdir = workdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile
        # Prepare a year, month and day for a ISO name timestamp.
        self.year = str(datetime.now().year).zfill(4)
        self.month = str(datetime.now().month).zfill(2)
        self.day = str(datetime.now().day).zfill(2)
        self.medium_name = '%s-%s%s%s.iso' % (name, self.year, self.month, self.day)
        self.digest_name = '%s.DIGESTS' % self.medium_name


    def isoit(self, alt_name = None):
        # Create the ISO with the default name unless an alt_name is given.
        if alt_name:
            self.medium_name = '%s-%s%s%s.iso' % (alt_name, self.year, self.month, self.day)
            self.digest_name = '%s.DIGESTS' % self.medium_name
        iso_path = os.path.join(self.workdir, 'iso')
        grub_path = os.path.join(iso_path, 'boot/grub')
        os.makedirs(grub_path, mode=0o755, exist_ok=False)
        #
        # 1. build initramfs image and copy it in
        #    locate a build script for the initramfs in self.libdir/scripts
        #    locate a busybox config script in self.libdir/scripts
        #    locate an init scripts in self.libdir/scripts
        #    copy in any kernel modules(?)
        #    find . | cpio -H newc -o | gzip -9 > iso/boot/initramfs.igz
        #
        # 2. make the squashfs image and copy it into the iso/boot
        squashfs_path = os.path.join(iso_path, 'rootfs')
        cmd = 'mksquashfs %s %s -xattrs -comp xz' % (self.portage_configroot, squashfs_path)
        Execute(cmd, timeout=None, logfile=self.logfile)
        #
        # 3. prepare the grub bootloader
        #    copy in stage2_eltorito into iso/boot/grub
        #    copy in menu.lst into iso/boot/grub
        #
        # 4. create the iso image
        #    mkisofs -R -b boot/grub/stage2_eltorito -no-emul-boot -boot-load-size 4 \
        #        -boot-info-table -o medium_pathname.iso iso
