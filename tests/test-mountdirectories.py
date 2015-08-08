#!/usr/bin/python
#
#    test-mountdirectories.py: this file is part of the GRS suite
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
import sys
sys.path.append(os.path.abspath('..'))

from grs import Execute
from grs import MountDirectories

if __name__ == "__main__":

    package = '/tmp/test-package'
    try:
        os.makedirs(package)
    except FileExistsError:
        pass
    empty_file = os.path.join(package, 'empty')
    open(empty_file, 'a').close()

    configroot = '/tmp/test-mountdirectories'
    directories = [ 'dev', 'dev/pts', 'dev/shm', 'proc', 'sys', 'usr/portage', 'usr/portage/packages' ]
    for d in directories:
        try:
            os.makedirs(os.path.join(configroot, d))
        except FileExistsError:
            pass
    alt_empty_file = os.path.join(configroot, 'usr/portage/packages/empty')

    md = MountDirectories(portage_configroot=configroot, package=package, logfile='/dev/null')

    md.umount_all()
    some_mounted, all_mounted = md.are_mounted()
    assert(some_mounted == False)
    assert(all_mounted == False)

    md.mount_all()
    some_mounted, all_mounted = md.are_mounted()
    assert(some_mounted == True)
    assert(all_mounted == True)

    # /tmp/test-package/aaa and /tmp/test-mountdirectories/usr/portage/packages/empty exist
    assert(os.path.isfile(alt_empty_file) == True)
    Execute('umount --force %s' % os.path.dirname(alt_empty_file))
    some_mounted, all_mounted = md.are_mounted()
    assert(some_mounted == True)
    assert(all_mounted == False)
    # /tmp/test-mountdirectories/usr/portage/packages/empty doesn't exist anymore
    assert(os.path.isfile(alt_empty_file) == False)

    assert(md.ismounted(package) == False)
    assert(md.ismounted(os.path.join(configroot, 'dev')) == True)

    md.umount_all()
    some_mounted, all_mounted = md.are_mounted()
    assert(some_mounted == False)
    assert(all_mounted == False)
