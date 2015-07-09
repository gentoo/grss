i#!/usr/bin/env python

import glob
import re
import shutil

class Rotator():
    """ doc here
        more doc
    """

    def rotate(self, obj):
        """ doc here
            more doc
        """
        objs = glob.glob('%s.*' % obj)
        indexed_obj = {}
        for o in objs:
            m = re.search('^.+\.(\d+)$', o)
            indexed_obj[int(m.group(1))] = o
        count = list(indexed_obj.keys())
        count.sort()
        count.reverse()
        for c in count:
            current_obj = indexed_obj[c]
            m = re.search('^(.+)\.\d+$', current_obj)
            next_obj = '%s.%d' % (m.group(1), c+1)
            shutil.move(current_obj, next_obj)
