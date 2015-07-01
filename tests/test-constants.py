#!/usr/bin/python

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

    print(CONST.nameservers)
    print(CONST.repo_uris)
    print(CONST.stage_uris)
    print(CONST.names)
    print(CONST.libdirs)
    print(CONST.logfiles)
    print(CONST.workdirs)
    print(CONST.kernelroots)
    print(CONST.portage_configroots)
