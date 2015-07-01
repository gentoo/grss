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
    def conf2file(config, s, portage_dir):
        """ doc here
            more doc
        """
        try:
            for (f, v) in config[s].items():
                # a '+' at the beginging means append to the file
                undecorated_f = re.sub('^\+', '', f)

                filepath = os.path.join(portage_dir, undecorated_f)
                dirpath  = os.path.dirname(filepath)
                os.makedirs(dirpath, mode=0o755, exist_ok=True)
                if f == undecorated_f or not os.path.exists(filepath):
                    with open(filepath, 'w') as g:
                        g.write('%s\n' % v)
                else:
                    with open(filepath, 'r+') as g:
                        for l in g.readlines():
                            if v == l.strip():
                                break
                        else:
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
            WorldConf.conf2file(config, s, portage_dir=CONST.PORTAGE_CONFIGDIR)


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
                # These packages are installed on the local system
                # but not in the portage tree anymore.
                print(p)

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

        env_slot_atoms = []
        for dirpath, dirnames, filenames in os.walk(CONST.PORTAGE_CONFIGDIR):
            # Only look at select files and directories.
            # TODO: This needs to be expanded as we come up
            # with a central class to deal with the internal
            # structure of /etc/portage.
            skip = True
            for p in ['env', 'package.accept_keywords', 'package.use']:
                if os.path.basename(dirpath) == p:
                    skip = False
            if skip:
                continue

            for f in filenames:
                fpath = os.path.realpath(os.path.join(dirpath, f))
                if f in slot_atoms:
                    os.remove(fpath)
                    if os.path.basename(dirpath) == 'env':
                        env_slot_atoms.append(f)
                    continue

        fpath = os.path.join(CONST.PORTAGE_CONFIGDIR, 'package.env')
        update = False
        with open(fpath, 'r') as g:
            lines = g.readlines()
            mylines = copy.deepcopy(lines)
            for l in lines:
                for slot_atom in env_slot_atoms:
                    if re.search(re.escape(slot_atom), l):
                        try:
                            mylines.remove(l)
                            update = True
                        except ValueError:
                            pass
        if update:
            with open(fpath, 'w') as g:
                g.writelines(mylines)
