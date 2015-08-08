#!/usr/bin/env python
#
#    setup.py: this file is part of the GRS suite
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

from distutils.core import setup

setup(
    name = 'grs',
    version = '0.1',
    description = 'Gentoo Release System Suite',
    long_description =
    """
    The Gentoo Reference System (GRS) Suite is a set of utilities for producing
    and maintaining identical Gentoo systems from a series of configuration files
    housed on a central git repository.
    """,
    url = 'https://wiki.gentoo.org/wiki/Project:Gentoo_Release_System',
    author = 'Anthony G. Basile',
    author_email = 'blueness@gentoo.org',
    license = 'GNU General Public License, Version 2',
    packages = ['grs'],
    scripts = ['bin/grsrun', 'bin/grsup', 'bin/clean-worldconf', \
        'bin/install-worldconf', 'bin/make-worldconf'],
    data_files = [('/etc/grs', ['conf/systems.conf'])]
) 
