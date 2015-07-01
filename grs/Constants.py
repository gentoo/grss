#!/use/bin/env python

import os
import sys
import configparser
from copy import deepcopy

CONFIG = '/etc/grs/systems.conf'

class Constants():
    """ doc here
        more doc
    """

    def __init__(self, configfile = CONFIG):
        if not os.path.isfile(configfile):
            sys.stderr.write('Configuration file %s not found\n' % configfile)
            sys.exit(1)
        self.config = configparser.ConfigParser(delimiters = ':', comment_prefixes = '#')
        self.config.read(configfile)

        self.names = list(self.config.sections())

        server    = 'http://distfiles.gentoo.org/'
        stagedir  = 'gentoo/releases/amd64/autobuilds/current-stage3-amd64-uclibc-hardened/'
        stagefile = 'stage3-amd64-uclibc-hardened-20150510.tar.bz2'
        default_stage_uri =  server + stagedir + stagefile

        space = {
            'nameserver'          : '8.8.8.8',
            'repo_uri'            : 'git://tweedledum.dyc.edu/grs',
            'stage_uri'           : default_stage_uri,
            'libdir'              : '/var/lib/grs/%s',
            'logfile'             : '/var/log/grs/%s.log',
            'tmpdir'              : '/var/tmp/grs/%s',
            'workdir'             : '/var/tmp/grs/%s/work',
            'package'             : '/var/tmp/grs/%s/packages',
            'kernelroot'          : '/var/tmp/grs/%s/kernel',
            'portage_configroot'  : '/var/tmp/grs/%s/system',
            'pidfile'             : '/run/grs-%s.pid'
        }

        for key in space:
            self.__dict__[key+'s'] = []

        for section in self.config.sections():
            overrides = dict(self.config[section].items())

            for key in space:
                if key in overrides:
                    value = overrides[key]
                else:
                    try:
                        value = space[key] % section
                    except TypeError:
                        value = space[key]
                self.__dict__[key+'s'].append(value)


    def __setattr__(self, key, value):
        if not key in self.__dict__:
            self.__dict__[key] = value
        else:
            pass


    def __getattr__(self, key, value = None):
        if key in self.__dict__:
            return deepcopy(self.__dict__[key])


    def __delattr__(self, key):
        if key in self.__dict__:
            pass


CONST = Constants()

CONST.PACKAGE_NAME        = "Gentoo Reference System"
CONST.PACKAGE_VERSION     = 0.0
CONST.PACKAGE_DESCRIPTION = "Update a GRS by cloning a predefined system."
CONST.BUG_REPORTS         = 'http://bugs.gentoo.org'

# The are defaults in case objects are instantiated without namespaces
# but they should not be used under normal working condidtions.
CONST.LIBDIR              = '/var/lib/grs'
CONST.LOGFILE             = '/var/log/grs.log'
CONST.TMPDIR              = '/var/tmp/grs'
CONST.WORKDIR             = '/var/tmp/grs/work'
CONST.PACKAGE             = '/var/tmp/grs/package'
CONST.KERNELROOT          = '/var/tmp/grs/kernel'
CONST.PORTAGE_CONFIGROOT  = '/var/tmp/grs/system'
CONST.PIDFILE             = '/run/grs.pid'

CONST.PORTAGE_CONFIGDIR   = '/etc/portage'
CONST.PORTAGE_DIRTYFILE   = '/etc/portage/.grs_dirty'
CONST.WORLD_CONFIG        = '/etc/grs/world.conf'
