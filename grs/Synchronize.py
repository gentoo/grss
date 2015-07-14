#!/usr/bin/env python

import os
from grs.Constants import CONST
from grs.Execute import Execute

class Synchronize():
    """ Either clone or pull a remote git repository for a GRS system.  """

    def __init__(self, remote_repo, branch, libdir = CONST.LIBDIR, logfile = CONST.LOGFILE):
        self.remote_repo = remote_repo
        self.branch = branch
        self.local_repo = libdir
        self.logfile = logfile

    def sync(self):
        if self.isgitdir():
            # If the local repo exists, then make it pristine an pull
            cmd = 'git -C %s reset HEAD --hard' % self.local_repo
            Execute(cmd, timeout=60, logfile=self.logfile)
            cmd = 'git -C %s clean -f -x -d' % self.local_repo
            Execute(cmd, timeout=60, logfile=self.logfile)
            cmd = 'git -C %s pull' % self.local_repo
            Execute(cmd, timeout=60, logfile=self.logfile)
        else:
            # else clone afresh.
            cmd = 'git clone %s %s' % (self.remote_repo, self.local_repo)
            Execute(cmd, timeout=60, logfile=self.logfile)
        # Make sure we're on the correct branch for the desired GRS system.
        cmd = 'git -C %s checkout %s' % (self.local_repo, self.branch)
        Execute(cmd, timeout=60, logfile=self.logfile)

    def isgitdir(self):
        """ If there is a .git/config file, assume its a local git repository. """
        git_configdir = os.path.join(self.local_repo, '.git')
        git_configfile = os.path.join(git_configdir, 'config')
        return os.path.isdir(git_configdir) and os.path.isfile(git_configfile)
