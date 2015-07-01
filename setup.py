#!/usr/bin/env python

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
    scripts = ['grsrun', 'grsup', 'clean-worldconf', 'install-worldconf', 'make-worldconf'],
    data_files = [('/etc/grs', ['systems.conf'])]
) 
