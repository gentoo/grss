#!/usr/bin/python
#
#    test-constants.py: this file is part of the GRS suite
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

from grs import CONST

if __name__ == "__main__":
    # Test that you can't change or delete an already defined constant
    original = CONST.WORKDIR
    CONST.WORKDIR = 'not original'
    assert CONST.WORKDIR == original
    del CONST.WORKDIR
    assert CONST.WORKDIR == original

    # Test that a non existant constant is None
    assert CONST.I_DONT_EXIST == None

    # Teat that you can add new constants
    original = 'new value'
    CONST.I_AM_NEW = original
    assert CONST.I_AM_NEW == original
    CONST.I_AM_NEW = 'not original'
    assert CONST.I_AM_NEW == original
    del CONST.I_AM_NEW
    assert CONST.I_AM_NEW == original

    print(CONST.repo_uris)
    print(CONST.stage_uris)
    print(CONST.names)
    print(CONST.libdirs)
    print(CONST.logfiles)
    print(CONST.workdirs)
    print(CONST.kernelroots)
    print(CONST.portage_configroots)
