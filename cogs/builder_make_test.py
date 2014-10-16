#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Fall 2014
# University of Colorado

import copy
import unittest
import os
import time
import random
import zipfile
import logging
import shutil

import test_common
import test_common_backend
import builder_test

import auth
import structs


class BuilderRunTestCase(builder_test.BuilderRunTestCase):

    def setUp(self):

        # Call Parent
        super(BuilderRunTestCase, self).setUp()

        # Create Test
        tst_dict = copy.copy(test_common.TEST_TESTDICT)
        tst_dict['maxscore'] = "10"
        tst_dict['builder'] = "make"
        tst_dict['tester'] = "script"
        self.tst = self.asn.create_test(tst_dict, owner=self.user)

        # Create Submission
        sub_dict = copy.copy(test_common.SUBMISSION_TESTDICT)
        self.sub = self.asn.create_submission(sub_dict, owner=self.user)

    def tearDown(self):

        # Cleanup
        self.sub.delete()
        self.tst.delete()

        # Call parent
        super(BuilderRunTestCase, self).tearDown()

    def test_null(self):

        data = copy.copy(test_common.RUN_TESTDICT)
        data['test'] = str(self.tst.uuid)
        run = self.sub.execute_run(data, owner=self.user)
        self.assertTrue(run)
        while not run.is_complete():
            time.sleep(1)
        out = run.get_dict()

        # Cleanup
        run.delete()

        # Check
        try:
            self.assertEqual(out['status'], "complete-error-builder_build")
            self.assertEqual(int(out['retcode']), 2)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

# Main
if __name__ == '__main__':
    unittest.main()
