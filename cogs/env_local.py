# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import shutil
import copy
import subprocess
import logging

import config

import backend_redis as backend
import structs
import env

_TST_DIR = "test"
_SUB_DIR = "submission"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Env(env.Env):

    def __init__(self, asn, sub, tst, run):

        # Call Parent
        super(Env, self).__init__(asn, sub, tst, run)

        # Setup Factory
        FileFactory = backend.UUIDFactory(structs.File)

        # Get Files
        sub_file_uuids = sub.list_files()
        sub_files = [FileFactory.from_existing(file_uuid) for file_uuid in sub_file_uuids]
        tst_file_uuids = tst.list_files()
        tst_files = [FileFactory.from_existing(file_uuid) for file_uuid in tst_file_uuids]

        # Setup Directories
        self.wd = os.path.abspath("{:s}/{:s}/".format(config.ENV_LOCAL_TMP_PATH, str(run).lower()))
        self.wd_tst = "{:s}/{:s}".format(self.wd, _TST_DIR)
        self.wd_sub = "{:s}/{:s}".format(self.wd, _SUB_DIR)
        os.makedirs(self.wd)
        os.makedirs(self.wd_tst)
        os.makedirs(self.wd_sub)

        # Copy Tester Files
        self.tst_files = []
        for fle in tst_files:
            self.tst_files.append(self.copy_fle(fle.get_dict(), self.wd_tst))

        # Copy Submission Files
        self.sub_files = []
        for fle in sub_files:
            self.sub_files.append(self.copy_fle(fle.get_dict(), self.wd_sub))

        # Clean ENV
        self._env_vars = {}
        for var in os.environ:
            if not var.startswith("COGS"):
                self._env_vars[var] = os.environ[var]

    def copy_fle(self, fle, dst_dir):
        new_fle = copy.copy(fle)
        src = os.path.abspath("{:s}".format(new_fle['path']))
        dst = os.path.abspath("{:s}/{:s}".format(dst_dir, fle['name']))
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copy(src, dst)
        new_fle['path'] = dst
        return new_fle

    def run_cmd(self, user_cmd, stdin=None):

        # Setup Sandbox
        sandbox_exe = config.ENV_LOCAL_SANDBOX_SCRIPT
        sandbox_src = "{:s}/{:s}".format(config.SCRIPTS_PATH, sandbox_exe)
        sandbox_fle = {}
        sandbox_fle['name'] = sandbox_exe
        sandbox_fle['path'] = sandbox_src
        sandbox_fle = self.copy_fle(sandbox_fle, self.wd)

        # Setup Sandboxing
        sudo_cmd = ['sudo', '-u', str(config.ENV_LOCAL_USER), '-g', str(config.ENV_LOCAL_GROUP)]
        sandbox_path = sandbox_fle['path']
        sandbox_cmd = [sandbox_path,
                       str(config.ENV_LOCAL_LIMIT_TIME_CPU),
                       str(config.ENV_LOCAL_LIMIT_TIME_WALL)]
        os.chmod(sandbox_path, 0775)

        # Change to WD
        owd = os.getcwd()
        msg = "Changing to directory '{:s}'".format(self.wd)
        logger.debug(self._format_msg(msg))
        os.chdir(self.wd)

        # Run Command
        full_cmd = sudo_cmd + sandbox_cmd + user_cmd
        msg = "Preparing to run '{:s}'".format(full_cmd)
        logger.info(self._format_msg(msg))
        p = subprocess.Popen(full_cmd, env=self._env_vars,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=stdin)
        stdout, stderr = p.communicate()
        ret = p.returncode

        # Change Back to OWD
        msg = "Changing back to directory '{:s}'".format(owd)
        logger.debug(self._format_msg(msg))
        os.chdir(owd)

        return ret, stdout, stderr


    def close(self):

        # Delete Submission Files
        for fle in self.sub_files:
            try:
                os.remove(fle['path'])
            except OSError:
                pass

        # Delete Tester Files
        for fle in self.tst_files:
            try:
                os.remove(fle['path'])
            except OSError:
                pass

        # Delete Directory
        shutil.rmtree(self.wd)
