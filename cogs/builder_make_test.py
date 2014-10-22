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

        # Run Test
        run = self.run_test(self.sub)
        out = run.get_dict()

        # Cleanup
        run.delete()

        # Check Output
        try:
            self.assertEqual(out['status'], "complete-error-builder_build")
            self.assertEqual(int(out['retcode']), 2)
            self.assertTrue(out['output'])
            self.assertIn("No targets specified and no makefile found" ,out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            self.print_fail(out)
            raise

    def test_makefile_empty(self):

        # Add Sub Files
        sub_files = [("hello_c/Makefile", 'makefile', None)]
        fles = self.add_files(sub_files, self.sub)

        # Run Test
        run = self.run_test(self.sub)
        out = run.get_dict()

        # Cleanup
        run.delete()
        for fle in fles:
            fle.delete()

        # Check Output
        try:
            self.assertEqual(out['status'], "complete-error-builder_build")
            self.assertEqual(int(out['retcode']), 2)
            self.assertTrue(out['output'])
            self.assertIn("No rule to make target" ,out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            self.print_fail(out)
            raise

    def test_makefile_good(self):

        # Add Sub Files
        sub_files = [("hello_c/Makefile", 'makefile', None),
                     ("hello_c/hello.c", 'source', None)]
        fles = self.add_files(sub_files, self.sub)

        # Run Test
        run = self.run_test(self.sub)
        out = run.get_dict()

        # Cleanup
        run.delete()
        for fle in fles:
            fle.delete()

        # Check Output
        try:
            self.assertEqual(out['status'], "complete-exception-tester_run")
            self.assertEqual(int(out['retcode']), -1)
            self.assertTrue(out['output'])
            self.assertIn("Module requires a test script file, but none found" ,out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            self.print_fail(out)
            raise

    def test_script_good(self):

        # Add Tst Files
        tst_files = [("grade_hello.py", 'script', None)]
        fles = self.add_files(tst_files, self.tst)

        # Add Sub Files
        sub_files = [("hello_c/Makefile", 'makefile', None),
                     ("hello_c/hello.c", 'source', None)]
        fles = self.add_files(sub_files, self.sub)

        # Run Test
        run = self.run_test(self.sub)
        out = run.get_dict()

        # Cleanup
        run.delete()
        for fle in fles:
            fle.delete()

        # Check Output
        try:
            self.assertEqual(out['status'], "complete")
            self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertIn("Score ---------------> 10" ,out['output'])
            self.assertEqual(float(out['score']), 10)
        except AssertionError:
            self.print_fail(out)
            raise

# Main
if __name__ == '__main__':
    unittest.main()
