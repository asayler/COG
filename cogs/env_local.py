# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import shutil
import copy

import config

import backend_redis as backend
import structs


_TST_DIR = "test"
_SUB_DIR = "submission"


class Env(object):

    def __init__(self, asn, sub, tst, run):

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

        # Setup Sandbox
        sandbox_exe = config.ENV_LOCAL_SANDBOX
        sandbox_src = "{:s}/{:s}".format(config.SCRIPT_PATH, sandbox_exe)
        sandbox_fle = {}
        sandbox_fle['name'] = sandbox_exe
        sandbox_fle['path'] = sandbox_src
        self.sandbox = self.copy_fle(sandbox_fle, self.wd)

        # Copy Tester Files
        self.tst_files = []
        for fle in tst_files:
            self.tst_files.append(self.copy_fle(fle.get_dict(), self.wd_tst))

        # Copy Submission Files
        self.sub_files = []
        for fle in sub_files:
            self.sub_files.append(self.copy_fle(fle.get_dict(), self.wd_sub))

        # Clean ENV
        self.env = {}
        for var in os.environ:
            if not var.startswith("COGS"):
                self.env[var] = os.environ[var]

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
