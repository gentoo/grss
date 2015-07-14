#!/usr/bin/env python

import datetime
import glob
import os
import re
import shutil

from grs.Constants import CONST
from grs.Rotator import Rotator

class Log(Rotator):
    """ Initilize logs, log messages, or rotate logs.  """

    def __init__(self, logfile = CONST.LOGFILE):
        self.logfile = logfile
        # Make sure the log directory exists
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        open(self.logfile, 'a').close()

    def log(self, msg, stamped = True):
        # If requested, stamp a log message with the unix time.
        if stamped:
            current_time = datetime.datetime.now(datetime.timezone.utc)
            unix_timestamp = current_time.timestamp()
            msg = '[%f] %s' % (unix_timestamp, msg)
        with open(self.logfile, 'a') as f:
            f.write('%s\n' % msg)


    def rotate_logs(self, upper_limit = 20):
        # Rotate all the previous logs
        self.full_rotate(self.logfile, upper_limit=upper_limit)
        open(self.logfile, 'a').close()
