#!/usr/bin/env python
#
#    Rotator.py: this file is part of the GRS suite
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

import glob
import re
import os
import shutil

class Rotator():
    """ Super class for rotating files or directories.  """

    def rotate(self, obj, upper_limit=20):
        """ Does the work of rotating objects fitting the pattern obj.(d+).

            obj -> The absolute path to the objects to be rotated.  The
            obj's are assumed to have a pattern obj.(d+) and does NOT
            include a bare obj not followed by a decimal.  (For that,
            use full_rotate() below).  Note that gaps in numbers are
            are preserved.  Eg.

                Old Name        New Name
                log             (untouched)
                log.0           log.1
                log.1           log.2
                log.3           log.4 (Note the gap is preserved.)
                log.4           log.5

            obj's paste an upper limit are deleted.
        """
        objs = glob.glob('%s.*' % obj)
        indexed_obj = {}
        for o in objs:
            m = re.search(r'^.+\.(\d+)$', o)
            indexed_obj[int(m.group(1))] = o
        count = list(indexed_obj.keys())
        count.sort()
        count.reverse()
        for c in count:
            current_obj = indexed_obj[c]
            if c >= upper_limit:
                try:
                    shutil.rmtree(current_obj)
                except NotADirectoryError:
                    os.unlink(current_obj)
                continue
            m = re.search(r'^(.+)\.\d+$', current_obj)
            next_obj = '%s.%d' % (m.group(1), c+1)
            shutil.move(current_obj, next_obj)


    def full_rotate(self, obj, upper_limit=20):
        """ Rotate both obj and obj.(d+). """
        self.rotate(obj, upper_limit=upper_limit)
        if os.path.exists(obj):
            shutil.move(obj, '%s.0' % obj)
