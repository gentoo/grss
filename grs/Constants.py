#!/use/bin/env python
#
#    Constants.py: this file is part of the GRS suite
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

import os
import configparser
from copy import deepcopy


class Constants():
    """ Read a global configuration file and set/override constants for
        each GRS spec.  These constants are exported in the form:

            CONST.repo_uris[x] contains the repo_uri for the xth GRS spec
            etc.

        Notice the 's' added to the list name to distinguish the list from
        the constant it holds.  Here the x is an integer corresponding to a
        section in a global config file, which by default is located at
        '/etc/grs/systes.conf'.  This file is in configparser format and
        each section introduces a new GRS namespace.  The default values
        for all possible constants in any given GRS namespace are defined
        by the space[] dictionary below, but these can be overridden using
        the item:value pairs from the section of any given GRS namespace.
        E.g. Suppose /etc/grs/systems.conf contains

        [my-cool-desktop]
        kernelroot : /tmp/kernel_src_tree

        [my-cool-server]
        package : /var/tmp/my-packages

        Then CONST.kernelroots[0] is '/tmp/kernel_src_tree' rather than the
        default value '/var/tmp/grs/my-cool-desktop/kernel'.  The remainder
        of the constants default as delineated in the space[] dictionary with
        %s replaced by 'my-cool-desktop'.  Similarly CONST.my-cool-servers[1]
        has package directory '/var/tmp/my-package' rather than the default
        value '/var/tmp/grs/my-cool-server/packages',

        Finally, the that class overrides __setattr__, __gettattr__ and
        __delattr__ so that you cannot add/change/delete constants in
        a GRS namespace.
    """

    def __init__(self, configfile='/etc/grs/systems.conf'):
        # Grab an alternative config file from the env var CONFIGFILE
        # TODO: I've designed myself into a bit of a corner here, and
        # there is no easy way of adding a command line option to grsrun
        # or grsup which propagates to this class.
        if 'CONFIGFILE' in os.environ:
            configfile = os.environ['CONFIGFILE']
        # If there's no config file, we're dead in the water.
        if not os.path.isfile(configfile):
            raise Exception('Configuration file %s not found\n' % configfile)

        self.config = configparser.ConfigParser(delimiters=':', comment_prefixes='#')
        self.config.read(configfile)

        # These values will probably fail in the future, but that's okay
        # because they really should never be used.  They live outside of
        # any GRS namespace and are just 'defaults'.
        server = 'http://distfiles.gentoo.org/'
        stagedir = 'releases/amd64/autobuilds/current-stage3-amd64-uclibc-hardened/'
        stagefile = 'stage3-amd64-uclibc-hardened-20150510.tar.bz2'
        default_stage_uri = server + stagedir + stagefile

        # This is the space of all possible constants for any given GRS namespace
        space = {
            'repo_uri'            : 'git://anongit.gentoo.org/proj/grs.git',
            'stage_uri'           : default_stage_uri,
            'libdir'              : '/var/lib/grs/%s',
            'logfile'             : '/var/log/grs/%s.log',
            'tmpdir'              : '/var/tmp/grs/%s',
            'workdir'             : '/var/tmp/grs/%s/work',
            'package'             : '/var/tmp/grs/%s/packages',
            'portage'             : '/var/db/repos/gentoo',
            'kernelroot'          : '/var/tmp/grs/%s/kernel',
            'portage_configroot'  : '/var/tmp/grs/%s/system',
            'pidfile'             : '/run/grs-%s.pid'
        }

        # We add an 's' to each list for a particular constant,
        # and initialize the list to be empty.
        for key in space:
            self.__dict__[key+'s'] = []

        # Each section is a 'namespace' corresponding to each GRS spec.
        # We export these in the CONST.names[] list.
        self.names = list(self.config.sections())

        # We go over all the sections in the config file.  The
        # order here had better be the same as self.names[], else
        # CONST.names[x] doesn't corresponde to the other CONST.foo[x]
        # for every x.
        for section in self.config.sections():
            overrides = dict(self.config[section].items())

            # Either we have an override value from the config
            # file, else we contruct a default name.
            for key in space:
                if key in overrides:
                    value = overrides[key]
                else:
                    # Either the default name has a slot %s to
                    # file or else it doesn't.
                    try:
                        value = space[key] % section
                    except TypeError:
                        value = space[key]
                # We're counting on the order in which we append here to
                # correspond to the GRS namespace for the key:value pair.
                self.__dict__[key+'s'].append(value)


    # Allow CONST.foo = bar only once!
    def __setattr__(self, key, value):
        if not key in self.__dict__:
            self.__dict__[key] = value
        else:
            pass

    # Don't retrieve the original else you can overwrite it,
    # rather deep copy it.
    def __getattr__(self, key, value=None):
        if key in self.__dict__:
            return deepcopy(self.__dict__[key])

    # You can't del(CONST.foo).
    def __delattr__(self, key):
        if key in self.__dict__:
            pass


# Instantiate once and export all our constant in CONST.
CONST = Constants()

# Constants outside any GRS namespace.
CONST.PACKAGE_NAME = "Gentoo Reference System"
CONST.PACKAGE_VERSION = 0.0
CONST.PACKAGE_DESCRIPTION = "Update a GRS by cloning a predefined system."
CONST.BUG_REPORTS = 'http://bugs.gentoo.org'

# The are defaults in case objects of other classes which depend on values
# of libdir, logfile, etc. are instantiated outside of any namespaces.
# They should not be needed under normal working condidtions.
CONST.LIBDIR = '/var/lib/grs'
CONST.LOGFILE = '/var/log/grs.log'
CONST.TMPDIR = '/var/tmp/grs'
CONST.WORKDIR = '/var/tmp/grs/work'
CONST.PACKAGE = '/var/tmp/grs/package'
CONST.PORTAGE = '/var/db/repos/gentoo'
CONST.KERNELROOT = '/var/tmp/grs/kernel'
CONST.PORTAGE_CONFIGROOT = '/var/tmp/grs/system'
CONST.PIDFILE = '/run/grs.pid'

# These are used by grsup and are hard coded values.
CONST.PORTAGE_CONFIGDIR = '/etc/portage'
CONST.PORTAGE_DIRTYFILE = '/etc/portage/.grs_dirty'
CONST.WORLD_CONFIG = '/etc/grs/world.conf'
CONST.GRS_CGROUP = 'grs'
CONST.GRS_CGROUPDIR = '/sys/fs/cgroup/grs'
