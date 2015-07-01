#!/usr/bin/env python

import os
import re
import shutil

from grs.Constants import CONST
from grs.Execute import Execute


class Kernel():

    def __init__(self, libdir = CONST.LIBDIR, portage_configroot = CONST.PORTAGE_CONFIGROOT, kernelroot = CONST.KERNELROOT, package = CONST.PACKAGE, logfile = CONST.LOGFILE):
        self.libdir = libdir
        self.portage_configroot = portage_configroot
        self.kernelroot = kernelroot
        self.package = package
        self.logfile = logfile
        self.kernel_config = os.path.join(self.libdir, 'scripts/kernel-config')


    def parse_kernel_config(self):
        with open(self.kernel_config, 'r') as f:
            for i in range(3):
                line = f.readline()
        m = re.search('^#\s+(\S+)\s+(\S+).+$', line)
        gentoo_version = m.group(2)
        try:
            m = re.search('(\S+?)-(\S+?)-(\S+)', gentoo_version)
            vanilla_version = m.group(1)
            flavor = m.group(2)
            revision = m.group(3)
            pkg_name = flavor + '-sources-' + vanilla_version + '-' + revision
        except AttributeError:
            m = re.search('(\S+?)-(\S+)', gentoo_version)
            vanilla_version = m.group(1)
            flavor = m.group(2)
            pkg_name = flavor + '-sources-' + vanilla_version
        pkg_name = '=sys-kernel/' + pkg_name
        return (gentoo_version, pkg_name)


    def kernel(self):
        (gentoo_version, pkg_name) = self.parse_kernel_config()

        kernel_source = os.path.join(self.kernelroot, 'usr/src/linux')
        image_dir     = os.path.join(self.kernelroot, gentoo_version)
        boot_dir      = os.path.join(image_dir, 'boot')
        modprobe_dir  = os.path.join(image_dir, 'etc/modprobe.d')
        modules_dir   = os.path.join(image_dir, 'lib/modules')

        # Remove any old image directory and create a boot directory
        # wich genkernel assumes is present.
        shutil.rmtree(image_dir, ignore_errors=True)
        os.makedirs(boot_dir, mode=0o755, exist_ok=True)

        cmd = 'emerge --nodeps -1n %s' % pkg_name
        emerge_env = { 'USE' : 'symlink', 'ROOT' : self.kernelroot, 'ACCEPT_KEYWORDS' : '**' }
        Execute(cmd, timeout=600, extra_env=emerge_env, logfile=self.logfile)

        # Build and install the image outside the portage configroot so
        # we can both rsync it in *and* tarball it for downloads.
        # TODO: add more options (eg splash and firmware), which can be
        # specified vi the kernel line in the build script.
        cmd = 'genkernel '
        cmd += '--logfile=/dev/null '
        cmd += '--no-save-config '
        cmd += '--makeopts=-j9 '
        cmd += '--no-firmware '
        cmd += '--symlink '
        cmd += '--no-mountboot '
        cmd += '--kernel-config=%s ' % self.kernel_config
        cmd += '--kerneldir=%s '     % kernel_source
        cmd += '--bootdir=%s '       % boot_dir
        cmd += '--module-prefix=%s ' % image_dir
        cmd += '--modprobedir=%s '   % modprobe_dir
        cmd += 'all'
        Execute(cmd, timeout=None, logfile=self.logfile)

        for dirpath, dirnames, filenames in os.walk(modules_dir):
            for filename in filenames:
                if filename.endswith('.ko'):
                    module = os.path.join(dirpath, filename)
                    cmd = 'objcopy -v --strip-unneeded %s' % module
                    Execute(cmd)

        # Copy the newly compiled kernel image and modules to portage configroot
        cmd = 'rsync -a %s/ %s' % (image_dir, self.portage_configroot)
        Execute(cmd, timeout=60, logfile=self.logfile)

        # Tar up the kernel image and modules and place them in package/linux-images
        linux_images = os.path.join(self.package, 'linux-images')
        os.makedirs(linux_images, mode=0o755, exist_ok=True)
        tarball_name = 'linux-image-%s.tar.xz' % gentoo_version
        tarball_path = os.path.join(linux_images, tarball_name)

        cwd = os.getcwd()
        os.chdir(image_dir)
        if os.path.isfile(tarball_path):
            os.unlink(tarball_path)
        cmd = 'tar -Jcf %s .' % tarball_path
        Execute(cmd, timeout=600, logfile=self.logfile)
        os.chdir(cwd)
