#!/usr/bin/env python

import configparser
import copy
import os
import portage
import re

from grs.Constants import CONST

class WorldConf():
    """ doc here
        more doc
    """

    @staticmethod
    def conf2file(config, s, portage_confdir):
        """ doc here
            more doc
        """
        try:
            for (f, v) in config[s].items():
                filepath = os.path.join(portage_confdir, f)
                dirpath  = os.path.dirname(filepath)
                os.makedirs(dirpath, mode=0o755, exist_ok=True)
                with open(filepath, 'w') as g:
                    g.write('%s\n' % v)
        except KeyError:
            pass


    @staticmethod
    def install():
        """ doc here
            more doc
        """
        config = configparser.RawConfigParser(delimiters=':', allow_no_value=True, comment_prefixes=None)
        config.read(CONST.WORLD_CONFIG)

        for s in config.sections():
            WorldConf.conf2file(config, s, portage_confdir=CONST.PORTAGE_CONFIGDIR)


    @staticmethod
    def clean():
        """ doc here
            more doc
        """
        portdb = portage.db[portage.root]["porttree"].dbapi
        vardb  = portage.db[portage.root]["vartree"].dbapi

        uninstalled = portdb.cp_all()
        for p in vardb.cp_all():
            try:
                uninstalled.remove(p)
            except ValueError:
                print('%s installed on local system, but not in portage repo anymore.' % p)

        slot_atoms = []
        for p in uninstalled:
            cpv = portdb.cp_list(p)[0]
            slotvar = portdb.aux_get(cpv, ['SLOT'])[0]
            try:
                m = re.search('(.+?)\/(.+)', slotvar)
                slot = m.group(1)
            except AttributeError:
                slot = slotvar
            slot_atoms.append(re.sub('[/:]', '_', '%s:%s' % (p, slot)))

        for dirpath, dirnames, filenames in os.walk(CONST.PORTAGE_CONFIGDIR):
            # Only look at select files and directories.
            # TODO: This needs to be expanded.
            if not os.path.basename(dirpath) in ['env', 'package.env', \
                    'package.accept_keywords', 'package.use', 'package.mask', \
                    'package.unmask']:
                continue

            for f in filenames:
                fpath = os.path.realpath(os.path.join(dirpath, f))
                if f in slot_atoms:
                    os.remove(fpath)
                    continue
