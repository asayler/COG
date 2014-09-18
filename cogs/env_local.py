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
_FILE_SANITIZERS = ["dos2unix", "mac2unix"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Env(env.Env):

    def __init__(self, asn, sub, tst, run):

        # Call Parent
        super(Env, self).__init__(asn, sub, tst, run)

        logger.info(self._format_msg("Creating env_local"))

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
        os.chmod(self.wd_sub, 0777)

        # Copy Tester Files
        self.tst_files = []
        for fle in tst_files:
            fle_cpy = self.copy_fle(fle.get_dict(), self.wd_tst)
            self.tst_files.append(fle_cpy)

        # Copy Submission Files
        self.sub_files = []
        for fle in sub_files:
            fle_cpy = self.copy_fle(fle.get_dict(), self.wd_sub)
            self.sub_files.append(fle_cpy)

        # Sanitze Files
        for fle in (self.tst_files + self.sub_files):
            for pgm in _FILE_SANITIZERS:
                cmd_sanitize = [pgm, fle['path']]
                p = subprocess.Popen(cmd_sanitize, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                ret = p.returncode
                if stdout:
                    logger.debug(self._format_msg(stdout))
                if stderr:
                    logger.debug(self._format_msg(stderr))
                if (ret != 0):
                    msg = ("Sanitize pgm '{:s}' failed ".format(pgm) +
                           "on file '{:s}': ".format(fle_cpy['name']) +
                           "{:s}".format(stderr))
                    logger.warning(self._format_msg(msg))

        # Clean ENV
        self._env_vars = {}
        for var in os.environ:
            if not var.startswith("COGS"):
                self._env_vars[var] = os.environ[var]

    def copy_fle(self, fle, dst_dir):

        new_fle = copy.copy(fle)

        # Setup Paths
        src = os.path.abspath("{:s}".format(new_fle['path']))
        dst = os.path.abspath("{:s}/{:s}".format(dst_dir, fle['name']))
        dst_dir = os.path.dirname(dst)
        logger.info(self._format_msg("Copying '{:s}' to '{:s}'".format(src, dst)))

        # Setup Dst
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        # Copy
        shutil.copy(src, dst)
        new_fle['path'] = dst

        # Return
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

        # Run Command
        full_cmd = sudo_cmd + sandbox_cmd + user_cmd
        msg = "Running '{:s}'".format(full_cmd)
        logger.info(self._format_msg(msg))
        p = subprocess.Popen(full_cmd, env=self._env_vars,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=stdin)
        stdout, stderr = p.communicate()
        ret = p.returncode

        return ret, stdout, stderr


    def close(self):

        logger.info(self._format_msg("Closing env_Local"))

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
