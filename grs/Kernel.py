#!/usr/bin/env python
#
#    Kernel.py: this file is part of the GRS suite
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
import re
import shutil

from grs.Constants import CONST
from grs.Execute import Execute


class Kernel():
    """ Build a linux-image pkg and install when building a system. """

    def __init__(
            self,
            libdir=CONST.LIBDIR,
            portage_configroot=CONST.PORTAGE_CONFIGROOT,
            kernelroot=CONST.KERNELROOT,
            package=CONST.PACKAGE,
            logfile=CONST.LOGFILE
    ):
        self.libdir = libdir
        self.portage_configroot = portage_configroot
        self.kernelroot = kernelroot
        self.package = package
        self.logfile = logfile
        self.kernel_config = os.path.join(self.libdir, 'scripts/kernel-config')
        self.busybox_config = os.path.join(self.libdir, 'scripts/busybox-config')
        self.genkernel_config = os.path.join(self.libdir, 'scripts/genkernel.conf')


    def parse_kernel_config(self):
        """ Parse the version to be built/installed from the kernel-config file. """
        with open(self.kernel_config, 'r') as _file:
            lines = _file.readlines()
        # Are we building a modular kernel or statically linked?
        has_modules = 'CONFIG_MODULES=y\n' in lines
        # The third line is the version line in the kernel config file.
        version_line = lines[2]
        # The version line looks like the following:
        # Linux/x86 4.0.6-hardened-r2 Kernel Configuration
        # The 2nd group contains the version.
        _match = re.search(r'^#\s+(\S+)\s+(\S+).+$', version_line)
        gentoo_version = _match.group(2)
        try:
            # Either the verison is of the form '4.0.6-hardened-r2' with two -'s
            _match = re.search(r'(\S+?)-(\S+?)-(\S+)', gentoo_version)
            vanilla_version = _match.group(1)
            flavor = _match.group(2)
            revision = _match.group(3)
            pkg_name = flavor + '-sources-' + vanilla_version + '-' + revision
        except AttributeError:
            # Or the verison is of the form '4.0.6-hardened' with one -
            _match = re.search(r'(\S+?)-(\S+)', gentoo_version)
            vanilla_version = _match.group(1)
            flavor = _match.group(2)
            pkg_name = flavor + '-sources-' + vanilla_version
        pkg_name = '=sys-kernel/' + pkg_name
        return (gentoo_version, pkg_name, has_modules)


    def kernel(self, arch='x86_64'):
        """ This emerges the kernel sources to a directory outside of the
            fledgeling system's portage configroot, builds and installs it
            to yet another external directory, bundles the kernel and modules
            as a .tar.xz in the packages directory for downloads via grsup,
            and finally installs it to the system's portage configroot.
        """
        # Grab the parsed verison and pkg atom.
        (gentoo_version, pkg_name, has_modules) = self.parse_kernel_config()

        # Prepare the paths to where we'll emerge and build the kernel,
        # as well as paths for genkernel.
        kernel_source = os.path.join(self.kernelroot, 'usr/src/linux')
        image_dir = os.path.join(self.kernelroot, gentoo_version)
        boot_dir = os.path.join(image_dir, 'boot')
        modprobe_dir = os.path.join(image_dir, 'etc/modprobe.d')
        modules_dir = os.path.join(image_dir, 'lib/modules')

        # The firmware directory, if it exists, will be in self.portage_configroot
        firmware_dir = os.path.join(self.portage_configroot, 'lib/firmware')

        # Prepare tarball filename and path.  If the tarball already exists,
        # don't rebuild/reinstall it.  Note: It should have been installed to
        # the system's portage configroot when it was first built, so no need
        # to reinstall it.
        linux_images = os.path.join(self.package, 'linux-images')
        tarball_name = 'linux-image-%s.tar.xz' % gentoo_version
        tarball_path = os.path.join(linux_images, tarball_name)
        if os.path.isfile(tarball_path):
            return

        # Remove any old kernel image directory and create a boot directory.
        # Note genkernel assumes a boot directory is present.
        shutil.rmtree(image_dir, ignore_errors=True)
        os.makedirs(boot_dir, mode=0o755, exist_ok=True)

        # emerge the kernel source.
        cmd = 'emerge --nodeps -1n %s' % pkg_name
        emerge_env = {'USE' : 'symlink', 'ROOT' : self.kernelroot, 'ACCEPT_KEYWORDS' : '**'}
        Execute(cmd, timeout=600, extra_env=emerge_env, logfile=self.logfile)

        # Build and install the image outside the portage configroot so
        # we can both rsync it in *and* tarball it for downloads via grsup.
        # NOTE: more options (eg splash and firmware), can be specified
        # via the kernel line in the build script.
        cmd = 'genkernel '
        cmd += '--logfile=/dev/null '
        cmd += '--no-save-config '
        cmd += '--makeopts=-j9 '
        cmd += '--symlink '
        cmd += '--no-mountboot '
        cmd += '--kernel-config=%s ' % self.kernel_config
        cmd += '--kerneldir=%s '     % kernel_source
        cmd += '--bootdir=%s '       % boot_dir
        cmd += '--module-prefix=%s ' % image_dir
        cmd += '--modprobedir=%s '   % modprobe_dir
        cmd += '--arch-override=%s ' % arch
        if os.path.isfile(self.busybox_config):
            cmd += '--busybox-config=%s ' % self.busybox_config
        if os.path.isfile(self.genkernel_config):
            cmd += '--config=%s ' % self.genkernel_config
        if  os.path.isdir(firmware_dir):
            cmd += '--firmware-dir=%s ' % firmware_dir
        if has_modules:
            cmd += 'all'
        else:
            cmd += 'bzImage'

        Execute(cmd, timeout=None, logfile=self.logfile)

        # Strip the modules to shrink their size enormously!
        # This will do nothing if there is not modules_dir
        for dirpath, dirnames, filenames in os.walk(modules_dir):
            for filename in filenames:
                if filename.endswith('.ko'):
                    module = os.path.join(dirpath, filename)
                    cmd = 'objcopy -v --strip-unneeded %s' % module
                    Execute(cmd)

        # Copy the newly compiled kernel image and modules to portage configroot
        cmd = 'rsync -aK %s/ %s' % (image_dir, self.portage_configroot)
        Execute(cmd, timeout=60, logfile=self.logfile)

        # Tar up the kernel image and modules and place them in package/linux-images
        os.makedirs(linux_images, mode=0o755, exist_ok=True)
        cwd = os.getcwd()
        os.chdir(image_dir)
        cmd = 'tar -Jcf %s .' % tarball_path
        Execute(cmd, timeout=600, logfile=self.logfile)
        os.chdir(cwd)
