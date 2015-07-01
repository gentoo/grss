#!/usr/bin/env python

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
