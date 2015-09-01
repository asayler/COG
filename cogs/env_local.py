# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import os.path
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
_WRK_DIR = "scratch"
_FILE_SANITIZERS = ["dos2unix", "mac2unix"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Env(env.Env):

    def __init__(self, asn, sub, tst, run):

        # Call Parent
        super(Env, self).__init__(asn, sub, tst, run)
        msg = "envmod_local: Initializing environment"
        logger.info(self._format_msg(msg))

        # Setup Factory
        FileFactory = backend.UUIDFactory(structs.File)

        # Get Files
        sub_file_uuids = sub.list_files()
        sub_files = [FileFactory.from_existing(file_uuid) for file_uuid in sub_file_uuids]
        tst_file_uuids = tst.list_files()
        tst_files = [FileFactory.from_existing(file_uuid) for file_uuid in tst_file_uuids]

        # Setup Directories
        self.wd = os.path.abspath(os.path.join(config.ENV_LOCAL_TMP_PATH, str(run).lower()))
        self.wd_tst = os.path.join(self.wd, _TST_DIR)
        self.wd_sub = os.path.join(self.wd, _SUB_DIR)
        self.wd_wrk = os.path.join(self.wd, _WRK_DIR)
        os.makedirs(self.wd)
        os.makedirs(self.wd_tst)
        os.makedirs(self.wd_sub)
        os.makedirs(self.wd_wrk)
        os.chmod(self.wd_sub, 0777) # TODO: Remove this
        os.chmod(self.wd_wrk, 0777)

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
                    msg = "envmod_local: '{:s}' stdout: {:s}".format(pgm, stdout)
                    logger.debug(self._format_msg(msg))
                if stderr:
                    msg = "envmod_local: '{:s}' stderr: {:s}".format(pgm, stderr)
                    logger.debug(self._format_msg(msg))
                if (ret != 0):
                    msg = "envmod_local: "
                    msg += "Sanitize pgm '{:s}' failed ".format(pgm)
                    msg += "on file '{:s}': ".format(fle_cpy['name'])
                    msg += "{:s}".format(stderr)
                    logger.warning(self._format_msg(msg))

        # Clean and Setup Env Vars
        self._env_vars = {}
        for var in os.environ:
            if var.startswith("COGS"):
                pass
            elif var.startswith("APACHE"):
                pass
            else:
                self._env_vars[var] = os.environ[var]
        self._env_vars['LANG'] = "C.UTF-8"
        self._env_vars['HOME'] = self.wd_wrk
        msg = "env_vars: {:s}".format(self._env_vars)
        logger.info(self._format_msg(msg))

    def copy_fle(self, fle, dst_dir):

        new_fle = copy.copy(fle)

        # Setup Paths
        src = os.path.abspath("{:s}".format(new_fle['path']))
        dst = os.path.abspath("{:s}/{:s}".format(dst_dir, fle['name']))
        dst_dir = os.path.dirname(dst)
        msg = "envmod_local: Copying '{:s}' to '{:s}'".format(src, dst)
        logger.info(self._format_msg(msg))

        # Setup Dst
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        # Copy
        shutil.copy(src, dst)
        new_fle['path'] = dst

        # Return
        return new_fle

    def run_cmd(self, user_cmd, stdin=None, combine=False, cwd=None):

        # Process Args
        if not cwd:
            cwd = self.wd_wrk

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

        # Setup Command
        if type(user_cmd) is list:
            if not len(user_cmd):
                msg = "user_cmd must not be empty"
                logger.error(self._format_msg(msg))
                raise(msg)
            full_cmd = sudo_cmd + sandbox_cmd + user_cmd
        elif type(user_cmd) is str:
            full_cmd = sudo_cmd + sandbox_cmd + [user_cmd]
        else:
            msg = "user_cmd must be list or str, not {:s}".format(type(user_cmd))
            logger.error(self._format_msg(msg))
            raise(msg)

        # Run Command
        msg = "envmod_local: Running '{:s}'".format(full_cmd)
        logger.info(self._format_msg(msg))
        if not combine:
            p = subprocess.Popen(full_cmd, env=self._env_vars, cwd=cwd, stdin=stdin,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(full_cmd, env=self._env_vars, cwd=cwd, stdin=stdin,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        ret = p.returncode

        return ret, stdout, stderr


    def close(self):

        logger.info(self._format_msg("envmod_local: Closing environment"))

        # Delete Submission Files
        for fle in self.sub_files:
            try:
                os.remove(fle['path'])
            except OSError as e:
                msg = "Failed to remove '{:s}': {:s}".format(fle['path'], str(e))
                logger.warning(self._format_msg(msg))

        # Delete Tester Files
        for fle in self.tst_files:
            try:
                os.remove(fle['path'])
            except OSError as e:
                msg = "Failed to remove '{:s}': {:s}".format(fle['path'], str(e))
                logger.warning(self._format_msg(msg))

        # Delete User-Generated Files and Directories
        self.run_cmd(['rm', '-rf',  self.wd])

        # Delete All Other Files and Directories
        try:
            shutil.rmtree(self.wd)
        except OSError as e:
            msg = "Failed to remove '{:s}': {:s}".format(self.wd, str(e))
            logger.warning(self._format_msg(msg))
