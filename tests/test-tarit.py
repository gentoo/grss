#!/usr/bin/env python
#
#    test-tarit.py: this file is part of the GRS suite
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

from grs import TarIt

if __name__ == "__main__":
    package = '/tmp/test-tarit'
    try:
        os.makedirs(package)
    except FileExistsError:
        pass
    for i in range(10):
        empty_file = os.path.join(package,'empty-%d' % i)
        with open(empty_file, 'w') as f:
            f.write('%d\n' % i)
            f.close()

    bi = TarIt('tar-test', portage_configroot=package, logfile='/dev/null')
    bi.tarit()
    bi.hashit()
