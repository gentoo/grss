#!/usr/bin/env python

import datetime
import glob
import os
import re
import shutil
from grs.Constants import CONST

class Log():

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
        logs = glob.glob('%s.*' % self.logfile)
        indexed_log = {}
        for l in logs:
            m = re.search('^.+\.(\d+)$', l)
            indexed_log[int(m.group(1))] = l
        count = list(indexed_log.keys())
        count.sort()
        count.reverse()
        for c in count:
            current_log = indexed_log[c]
            m = re.search('^(.+)\.\d+$', current_log)
            next_log = '%s.%d' % (m.group(1), c+1)
            shutil.move(current_log, next_log)
        if os.path.isfile(self.logfile):
            shutil.move(self.logfile, '%s.0' % self.logfile)
        open('%s' % self.logfile, 'a').close()
