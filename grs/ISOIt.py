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
import shutil
from datetime import datetime
from grs.Constants import CONST
from grs.Execute import Execute
from grs.HashIt import HashIt

class ISOIt(HashIt):
    """ Create a bootable ISO of the system. """

    def __init__(self, name, libdir = CONST.LIBDIR, tmpdir = CONST.TMPDIR, \
            portage_configroot = CONST.PORTAGE_CONFIGROOT, logfile = CONST.LOGFILE):
        self.libdir = libdir
        self.tmpdir = tmpdir
        self.portage_configroot = portage_configroot
        self.logfile = logfile
        # Prepare a year, month and day for a ISO name timestamp.
        self.year = str(datetime.now().year).zfill(4)
        self.month = str(datetime.now().month).zfill(2)
        self.day = str(datetime.now().day).zfill(2)
        self.medium_name = '%s-%s%s%s.iso' % (name, self.year, self.month, self.day)
        self.digest_name = '%s.DIGESTS' % self.medium_name


    def initramfs(self, isoboot_dir):
        """ TODO """
        # Paths to where we'll build busybox and the initramfs.
        busybox_root     = os.path.join(self.tmpdir, 'busybox')
        busybox_path     = os.path.join(busybox_root, 'bin/busybox')
        makeprofile_path = os.path.join(busybox_root, 'etc/portage/make.profile')
        savedconfig_dir  = os.path.join(busybox_root, 'etc/portage/savedconfig/sys-apps')
        savedconfig_path = os.path.join(savedconfig_dir, 'busybox')
        busybox_config   = os.path.join(self.libdir, 'scripts/busybox-config')

        # Remove any old busybox build directory and prepare new one.
        shutil.rmtree(busybox_root, ignore_errors=True)
        os.makedirs(savedconfig_dir, mode=0o755, exist_ok=True)
        shutil.copy(busybox_config, savedconfig_path)

        # Emerge busybox.
        os.symlink('/usr/portage/profiles/hardened/linux/amd64', makeprofile_path)
        cmd = 'emerge --nodeps -1q busybox'
        emerge_env = { 'USE' : '-* savedconfig', 'ROOT' : busybox_root,
            'PORTAGE_CONFIGROOT' : busybox_root }
        Execute(cmd, timeout=600, extra_env=emerge_env, logfile=self.logfile)

        # Remove any old initramfs root and prepare a new one.
        initramfs_root = os.path.join(self.tmpdir, 'initramfs')
        shutil.rmtree(initramfs_root, ignore_errors=True)
        root_paths = ['bin', 'dev', 'etc', 'mnt/cdrom', 'mnt/squashfs', 'mnt/tmpfs',
            'proc', 'sbin', 'sys', 'tmp', 'usr/bin', 'usr/sbin', 'var', 'var/run']
        for p in root_paths:
            d = os.path.join(initramfs_root, p)
            os.makedirs(d, mode=0o755, exist_ok=True)

        # Copy the static busybox to the initramfs root.
        # TODO: we are assuming a static busybox, so we should check.
        busybox_initramfs_path = os.path.join(initramfs_root, 'bin/busybox')
        shutil.copy(busybox_path, busybox_initramfs_path)
        os.chmod(busybox_initramfs_path, 0o0755)
        cmd = 'chroot %s /bin/busybox --install -s' % initramfs_root
        Execute(cmd, timeout=60, logfile=self.logfile)

        # Copy the init script to the initramfs root.
        initscript_path = os.path.join(self.libdir, 'scripts/initramfs-init')
        init_initramfs_path = os.path.join(initramfs_root, 'init')
        shutil.copy(initscript_path, init_initramfs_path)
        os.chmod(init_initramfs_path, 0o0755)

        # TODO: we are assuming a static kernel and so not copying in
        # any modules.  This is where we should copy in modules.

        # cpio-gzip the initramfs root to the iso boot dir
        initramfs_path = os.path.join(isoboot_dir, 'initramfs')
        cwd = os.getcwd()
        os.chdir(initramfs_root)
        cmd = 'find . -print | cpio -H newc -o | gzip -9 > %s' % initramfs_path
        # Piped commands must be run in a shell.
        Execute(cmd, timeout=600, logfile=self.logfile, shell=True)
        os.chdir(cwd)


    def isoit(self, alt_name = None):
        # Create the ISO with the default name unless an alt_name is given.
        if alt_name:
            self.medium_name = '%s-%s%s%s.iso' % (alt_name, self.year, self.month, self.day)
            self.digest_name = '%s.DIGESTS' % self.medium_name
        iso_dir     = os.path.join(self.tmpdir, 'iso')
        isoboot_dir = os.path.join(iso_dir, 'boot')
        isogrub_dir = os.path.join(isoboot_dir, 'grub')
        shutil.rmtree(iso_dir, ignore_errors=True)
        os.makedirs(isogrub_dir, mode=0o755, exist_ok=False)

        # 1. build initramfs image and copy it in
        self.initramfs(isoboot_dir)

        # 2. Move the kernel image into the iso/boot directory.
        # TODO: we are assuming a static kernel
        kernelimage_dir  = os.path.join(self.portage_configroot, 'boot')
        kernelimage_path = os.path.join(kernelimage_dir, 'kernel')
        shutil.copy(kernelimage_path, isoboot_dir)
        # If this fails, we'll have to rebuild the kernel!
        #shutil.rmtree(kernelimage_dir, ignore_errors=True)

        # 3. make the squashfs image and copy it into the iso/boot
        squashfs_path = os.path.join(iso_dir, 'rootfs')
        cmd = 'mksquashfs %s %s -xattrs -comp xz' % (self.portage_configroot, squashfs_path)
        Execute(cmd, timeout=600, logfile=self.logfile)

        # 4. Emerge grub:0 to grab stage2_eltorito
        grub_root     = os.path.join(self.tmpdir, 'grub')
        eltorito_path = os.path.join(grub_root, 'boot/grub/stage2_eltorito')
        menulst_path  = os.path.join(self.libdir, 'scripts/menu.lst')
        cmd = 'emerge --nodeps -1q grub:0'
        emerge_env = { 'USE' : '-* savedconfig', 'ROOT' : grub_root }
        Execute(cmd, timeout=600, extra_env=emerge_env, logfile=self.logfile)
        shutil.copy(eltorito_path, isogrub_dir)
        shutil.copy(menulst_path, isogrub_dir)

        # 5. create the iso image
        args  = '-R '                           # Rock Ridge protocol
        args += '-b boot/grub/stage2_eltorito ' # El Torito boot image
        args += '-no-emul-boot '                # No disk emulation for El Torito
        args += '-boot-load-size 4 '            # 4x512-bit sectors for no-emulation mode
        args += '-boot-info-table '             # Create El Torito boot info table
        medium_path = os.path.join(self.tmpdir, self.medium_name)
        cmd = 'mkisofs %s -o %s %s' % (args, medium_path, iso_dir)
        Execute(cmd, timeout=600, logfile=self.logfile)
