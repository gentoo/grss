#!/usr/bin/python

import os
import sys
sys.path.append(os.path.abspath('..'))

import hashlib
import shutil
from grs import Log

logdir = '/tmp/test-log'

def doit(stamped = False):
    try:
        shutil.rmtree(logdir)
    except FileNotFoundError:
        pass
    os.makedirs(logdir)
    logfile = os.path.join(logdir, 'test.log')

    lo = Log(logfile)
    for i in range(10):
        lo.log('first %d' % i, stamped)

    lo.rotate_logs()
    lo.rotate_logs()
    lo.rotate_logs()
    for i in list(range(9,-1,-1)):
        lo.log('second %d' % i, stamped)


def hashtest(expect_pass = True):
    m = hashlib.md5()
    for i in [ '', '.0', '.1', '.2']:
        log = os.path.join(logdir, 'test.log%s' % i)
        with open(log, 'r') as f:
            m.update(f.read().encode('ascii'))
    if expect_pass:
        assert(m.hexdigest() == '485b8bf3a9e08bd5ccfdff7e1a8fe4e1')
    else:
        assert(m.hexdigest() != '485b8bf3a9e08bd5ccfdff7e1a8fe4e1')

if __name__ == "__main__":
    doit(stamped=False)
    hashtest(expect_pass=True)
    doit(stamped=True)
    hashtest(expect_pass=False)
