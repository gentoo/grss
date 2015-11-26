#!/usr/bin/env python
#
#    WorldConf.py: this file is part of the GRS suite
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

import configparser
import os
import portage
import re

from grs.Constants import CONST

class WorldConf():
    """ Manage files in /etc/portage based on /etc/grs/world.conf """

    # TODO: This needs to be expanded.
    manageddirs = ['env', 'package.env', 'package.accept_keywords', \
        'package.use', 'package.mask', 'package.unmask']

    @staticmethod
    def install():
        """ Restore /etc/portage to a prestine stage (removing all files
            in manageddirs, and copy in all files specified in world.conf.
        """
        # This is harsh, but we need to start from a clean slate because
        # world.conf can drop sections.  If it does, then those files are
        # orphaned and can inject flags/envvars which are problematic.
        for directory in WorldConf.manageddirs:
            dpath = os.path.join(CONST.PORTAGE_CONFIGDIR, directory)
            if not os.path.isdir(dpath):
                continue
            for _file in os.listdir(dpath):
                fpath = os.path.join(dpath, _file)
                if os.path.isfile(fpath):
                    os.remove(fpath)

        # Now we can read world.conf and populate an empty /etc/portage.
        config = configparser.RawConfigParser(
            delimiters=':', allow_no_value=True, comment_prefixes=None
        )
        config.read(CONST.WORLD_CONFIG)
        for _section in config.sections():
            for (directory, value) in config[_section].items():
                p_slot_atom = re.sub(r'[/:]', '_', _section)
                dpath = os.path.join(CONST.PORTAGE_CONFIGDIR, directory)
                fpath = os.path.join(dpath, p_slot_atom)
                os.makedirs(dpath, mode=0o755, exist_ok=True)
                with open(fpath, 'w') as _file:
                    _file.write('%s\n' % value)


    @staticmethod
    def clean():
        """ Remove any files from /etc/portage that are unnecessary, ie that
            do not correspond to installed pkgs.
        """
        # We need to look at all portage provide pkgs and all installed pkgs.
        portdb = portage.db[portage.root]["porttree"].dbapi
        vardb = portage.db[portage.root]["vartree"].dbapi

        # Remove all installed pkgs from the set of all portage packages.
        uninstalled = portdb.cp_all()
        for _cp in vardb.cp_all():
            try:
                uninstalled.remove(_cp)
            except ValueError:
                print('%s installed on local system, but not in portage repo anymore.' % _cp)

        # Construct a list of canonical named files for uninstalled pkgs.
        slot_atoms = []
        for _cp in uninstalled:
            try:
                _cpv = portdb.cp_list(_cp)[0]
            except IndexError:
                print('Package with no ebuilds: %s' % _cp)
                continue
            slotvar = portdb.aux_get(_cpv, ['SLOT'])[0]
            try:
                _match = re.search(r'(.+?)\/(.+)', slotvar)
                slot = _match.group(1)
            except AttributeError:
                slot = slotvar
            slot_atoms.append(re.sub(r'[/:]', '_', '%s:%s' % (_cp, slot)))

        # Also let's get a list of all the possible canonical file names
        config = configparser.RawConfigParser(
            delimiters=':', allow_no_value=True, comment_prefixes=None
        )
        config.read(CONST.WORLD_CONFIG)
        canon = []
        for _section in config.sections():
            p_slot_atom = re.sub(r'[/:]', '_', _section)
            canon.append(p_slot_atom)

        # Walk through all files in /etc/portage and remove any files for uninstalled pkgs.
        for dirpath, dirnames, filenames in os.walk(CONST.PORTAGE_CONFIGDIR):
            # Only look at select files and directories.
            if not os.path.basename(dirpath) in WorldConf.manageddirs:
                continue

            # Remove all filenames that match uninstalled slot_atoms or are not in the canon
            for _file in filenames:
                fpath = os.path.realpath(os.path.join(dirpath, _file))
                if _file in slot_atoms or not _file in canon:
                    os.remove(fpath)
