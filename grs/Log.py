#!/usr/bin/env python

import datetime
import glob
import os
import re
import shutil

from grs.Constants import CONST
from grs.Rotator import Rotator

class Log(Rotator):

    def __init__(self, logfile = CONST.LOGFILE):
        self.logfile = logfile
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        open(self.logfile, 'a').close()


    def log(self, msg, stamped = True):
        if stamped:
            current_time = datetime.datetime.now(datetime.timezone.utc)
            unix_timestamp = current_time.timestamp()
            msg = '[%f] %s' % (unix_timestamp, msg)
        with open(self.logfile, 'a') as f:
            f.write('%s\n' % msg)


    def rotate_logs(self):
        self.rotate(self.logfile)
        if os.path.isfile(self.logfile):
            shutil.move(self.logfile, '%s.0' % self.logfile)
        open('%s' % self.logfile, 'a').close()
