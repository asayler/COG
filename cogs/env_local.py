# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import shutil
import copy

_LOC_DIR = "/tmp/cogs/"

import backend_redis as backend
import structs

class Env(object):

    def __init__(self, asn, sub, tst, run):

        # Setup Factory
        FileFactory = backend.UUIDFactory(structs.File)

        # Get Files
        sub_file_uuids = sub.list_files()
        sub_files = [FileFactory.from_existing(file_uuid) for file_uuid in sub_file_uuids]
        tst_file_uuids = tst.list_files()
        tst_files = [FileFactory.from_existing(file_uuid) for file_uuid in tst_file_uuids]

        # Save File Paths
        self.tst_files = []
        self.sub_files = []

        # Setup Working Directory
        self.wd = os.path.abspath("{:s}/{:s}/".format(_LOC_DIR, str(run).lower()))
        os.makedirs(self.wd)

        # Copy Submission Files
        for fle in sub_files:
            self.sub_files.append(self.copy_to_wd(fle))

        # Copy Tester Files
        for fle in tst_files:
            self.tst_files.append(self.copy_to_wd(fle))

    def copy_to_wd(self, fle):
        new_fle = fle.get_dict()
        src = os.path.abspath("{:s}".format(new_fle['path']))
        dst = os.path.abspath("{:s}/{:s}".format(self.wd, fle['name']))
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
