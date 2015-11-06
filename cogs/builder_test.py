#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Fall 2014
# University of Colorado


import copy
import os
import time

import test_common

import auth
import structs


class BuilderTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(BuilderTestCase, self).setUp()

        # Setup Auth
        self.auth = auth.Auth()

        # Setup Server
        self.srv = structs.Server()

        # Create User
        self.user = self.auth.create_user(test_common.USER_TESTDICT,
                                          username="testuser",
                                          password="testpass",
                                          authmod="test")

    def tearDown(self):

        # Cleanup
        self.user.delete()
        self.srv.close()

        # Call parent
        super(BuilderTestCase, self).tearDown()


class BuilderRunTestCase(BuilderTestCase):

    def setUp(self):

        # Call Parent
        super(BuilderRunTestCase, self).setUp()

        # Setup Assignment
        asn_dict = copy.copy(test_common.ASSIGNMENT_TESTDICT)
        asn_dict['env'] = "local"
        self.asn = self.srv.create_assignment(asn_dict, owner=self.user)

    def tearDown(self):

        # Cleanup
        self.asn.delete()

        # Call Parent
        super(BuilderRunTestCase, self).tearDown()

    def add_files(self, input_files, obj):

        fles = []
        for input_file in input_files:
            path, key, name = input_file
            src_path = os.path.abspath("{:s}/{:s}".format(test_common.TEST_INPUT_PATH, path))
            data = copy.copy(test_common.FILE_TESTDICT)
            if key:
                data['key'] = key
            if name:
                data['name'] = name
            fle = self.srv.create_file(data, src_path=src_path, owner=self.user)
            fles.append(fle)
        uuids = [str(fle.uuid) for fle in fles]
        obj.add_files(uuids)
        return fles

    def run_test(self, sub):

        data = copy.copy(test_common.RUN_TESTDICT)
        data['test'] = str(self.tst.uuid)
        run = sub.execute_run(data, owner=self.user)
        self.assertTrue(run)
        while not run.is_complete():
            time.sleep(1)
        return run

    def print_fail(self, out):
        print()
        print("run = {:s}".format(out))
        print("{:s}".format(out['output']))
