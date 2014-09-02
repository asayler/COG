#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest
import werkzeug
import os
import time
import multiprocessing
import random
import zipfile
import logging

import test_common
import test_common_backend

import auth
import structs


class StructsTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(StructsTestCase, self).setUp()

        # Setup Auth
        self.auth = auth.Auth()

        # Create User
        self.testuser = self.auth.create_user(test_common.USER_TESTDICT,
                                             username="testuser",
                                             password="testpass",
                                             authmod="test")

        # Setup Server
        self.srv = structs.Server()

        # Setup Worker Pool
        self.workers = None

    def tearDown(self):

        # Cleanup Server
        self.srv.close()

        # Cleanup User
        self.testuser.delete()

        # Call parent
        super(StructsTestCase, self).tearDown()

    def _create_zip(self, zip_path, file_paths):

        if os.path.exists(zip_path):
            raise Exception("{:s} already exists".format(zip_path))
        with zipfile.ZipFile(zip_path, 'w') as archive:
            for file_path in file_paths:
                file_name = os.path.relpath(file_path, test_common.TEST_INPUT_PATH)
                archive.write(file_path, file_name)


class ServerTestCase(test_common_backend.SubMixin,
                     StructsTestCase):

    def setUp(self):
        super(ServerTestCase, self).setUp()

    def tearDown(self):
        super(ServerTestCase, self).tearDown()

    def test_files(self):
        src_file = open("./Makefile", 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")
        self.subHashDirectHelper(self.srv.create_file,
                                 self.srv.get_file,
                                 self.srv.list_files,
                                 test_common.FILE_TESTDICT,
                                 extra_kwargs={'file_obj': file_obj, 'owner': self.testuser})
        file_obj.close()

    def test_reporters(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['asn_id'] = test_common.REPMOD_MOODLE_ASN
        self.subHashDirectHelper(self.srv.create_reporter,
                                 self.srv.get_reporter,
                                 self.srv.list_reporters,
                                 data,
                                 extra_kwargs={'owner': self.testuser})

    def test_assignments(self):
        self.subHashDirectHelper(self.srv.create_assignment,
                                 self.srv.get_assignment,
                                 self.srv.list_assignments,
                                 test_common.ASSIGNMENT_TESTDICT,
                                 extra_kwargs={'owner': self.testuser})

    def test_asn_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.testuser)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 asn.list_tests,
                                 test_common.TEST_TESTDICT,
                                 extra_kwargs={'owner': self.testuser})
        asn.delete()

    def test_srv_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.testuser)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 self.srv.list_tests,
                                 test_common.TEST_TESTDICT,
                                 extra_kwargs={'owner': self.testuser})
        asn.delete()

    def test_asn_submissions(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.testuser)
        self.subHashDirectHelper(asn.create_submission,
                                 self.srv.get_submission,
                                 asn.list_submissions,
                                 test_common.SUBMISSION_TESTDICT,
                                 extra_kwargs={'owner': self.testuser})
        asn.delete()

    def test_srv_submissions(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.testuser)
        self.subHashDirectHelper(asn.create_submission,
                                 self.srv.get_submission,
                                 self.srv.list_submissions,
                                 test_common.SUBMISSION_TESTDICT,
                                 extra_kwargs={'owner': self.testuser})
        asn.delete()


class FileTestCase(test_common_backend.UUIDHashMixin,
                   StructsTestCase):

    def setUp(self):

        # Call Parent
        super(FileTestCase, self).setUp()

        # Setup Test File
        file_key = "test"
        file_name = "test1.txt"
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        file_stream = open(file_path, 'rb')
        self.file_obj = werkzeug.datastructures.FileStorage(stream=file_stream,
                                                            filename=file_name,
                                                            name=file_key)

    def tearDown(self):

        # Cleanup
        self.file_obj.close()

        # Call Parent
        super(FileTestCase, self).tearDown()

    def test_create_file(self):
        self.hashCreateHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.testuser})

    def test_get_file(self):
        self.hashGetHelper(self.srv.create_file,
                           self.srv.get_file,
                           test_common.FILE_TESTDICT,
                           extra_kwargs={'file_obj': self.file_obj, 'owner': self.testuser})

    def test_update_file(self):
        self.hashUpdateHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.testuser})

    def test_delete_file(self):
        self.hashDeleteHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.testuser})

    def _run_zip_test(self, file_names):

        # Check Input
        file_paths = {}
        for file_name in file_names:
            file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
            file_paths[file_name] = file_path

        # Setup Zip
        archive_name = "test.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, file_paths.values())

        try:

            # Open Zip
            archive_key = "extract"
            archive_stream = open(archive_path, 'rb')
            archive_obj = werkzeug.datastructures.FileStorage(stream=archive_stream,
                                                              filename=archive_name,
                                                              name=archive_key)

            # Create from Zip
            fles = self.srv.create_files({}, archive_obj=archive_obj, owner=self.testuser)
            archive_obj.close()

            # Verify Output
            self.assertTrue(fles)
            self.assertEqual(len(fles), len(file_paths))
            for fle in fles:
                file_path = file_paths.pop(fle['name'], None)
                self.assertTrue(file_path, "Name '{:s}' not in input files".format(fle['name']))
                self.assertEqual(fle['key'], "from_{:s}".format(archive_name))
                self.assertTrue(os.path.exists(fle['path']))
                self.assertEqual(os.path.getsize(fle['path']), os.path.getsize(file_path))

        except Exception as e:
            raise
        finally:
            # Cleanup
            os.remove(archive_path)

    def test_zip_single(self):
        self._run_zip_test(['test1.txt'])

    def test_zip_multi(self):
        self._run_zip_test(['test1.txt', 'test2.txt', 'test3.txt'])

    def test_zip_dir_single(self):
        self._run_zip_test(['dir1/test1.txt'])

    def test_zip_dir_multi(self):
        self._run_zip_test(['dir2/test1.txt', 'dir2/test2.txt', 'dir2/test3.txt'])

    def test_zip_dir_nested(self):
        self._run_zip_test(['dir3/test1.txt', 'dir3/subdir/test2.txt', 'dir3/subdir/test3.txt'])


class ReporterTestCase(test_common_backend.UUIDHashMixin,
                       StructsTestCase):

    def setUp(self):

        super(ReporterTestCase, self).setUp()

        self.data = copy.copy(test_common.REPORTER_TESTDICT)
        self.data['mod'] = "moodle"
        self.data['asn_id'] = test_common.REPMOD_MOODLE_ASN

        self.student = self.auth.create_user(test_common.USER_TESTDICT,
                                             username=test_common.AUTHMOD_MOODLE_STUDENT_USERNAME,
                                             password=test_common.AUTHMOD_MOODLE_STUDENT_PASSWORD,
                                             authmod="moodle")

    def tearDown(self):
        self.student.delete()
        super(ReporterTestCase, self).tearDown()

    def test_create_reporter(self):
        self.hashCreateHelper(self.srv.create_reporter,
                              self.data,
                              extra_kwargs={'owner': self.testuser})

    def test_get_reporter(self):
        self.hashGetHelper(self.srv.create_reporter,
                           self.srv.get_reporter,
                           self.data,
                           extra_kwargs={'owner': self.testuser})

    def test_update_reporter(self):
        self.hashUpdateHelper(self.srv.create_reporter,
                              self.data,
                              extra_kwargs={'owner': self.testuser})

    def test_delete_reporter(self):
        self.hashDeleteHelper(self.srv.create_reporter,
                              self.data,
                              extra_kwargs={'owner': self.testuser})

    def test_file_report(self):
        grade = (random.randint(0,1000) / 100.0)
        comments = "Tested via test_file_report on {:s}.".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(self.data, owner=self.testuser)
        reporter.file_report(self.student, grade, comments)
        reporter.delete()

class AssignmentTestCase(test_common_backend.UUIDHashMixin,
                         StructsTestCase):

    def setUp(self):
        super(AssignmentTestCase, self).setUp()

    def tearDown(self):
        super(AssignmentTestCase, self).tearDown()

    def test_create_assignment(self):
        self.hashCreateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_get_assignment(self):
        self.hashGetHelper(self.srv.create_assignment,
                           self.srv.get_assignment,
                           test_common.ASSIGNMENT_TESTDICT,
                           extra_kwargs={'owner': self.testuser})

    def test_update_assignment(self):
        self.hashUpdateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_delete_assignment(self):
        self.hashDeleteHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              extra_kwargs={'owner': self.testuser})


class TestTestCase(test_common_backend.SubMixin,
                   test_common_backend.UUIDHashMixin,
                   StructsTestCase):

    def setUp(self):

        # Call Parent
        super(TestTestCase, self).setUp()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.testuser)

        # Create Files
        file_key = "test"
        file_name = "test1.txt"
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        file_stream = open(file_path, 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_stream,
                                                       filename=file_name,
                                                       name=file_key)
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, file_obj=file_obj, owner=self.testuser).uuid))
        file_obj.close()

        # Create Reporters
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['asn_id'] = test_common.REPMOD_MOODLE_ASN
        self.reporters = set([])
        for i in range(10):
            self.reporters.add(str(self.srv.create_reporter(data, owner=self.testuser).uuid))

    def tearDown(self):

        # Delete Reporters
        for rpt_uuid in self.reporters:
            rpt = self.srv.get_reporter(rpt_uuid)
            rpt.delete()

        # Delete Files
        for fle_uuid in self.files:
            fle = self.srv.get_file(fle_uuid)
            fle.delete()

        # Call Parent
        super(TestTestCase, self).tearDown()

    def test_create_test(self):
        self.hashCreateHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_get_test(self):
        self.hashGetHelper(self.asn.create_test,
                           self.srv.get_test,
                           test_common.TEST_TESTDICT,
                           extra_kwargs={'owner': self.testuser})

    def test_update_test(self):
        self.hashUpdateHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_delete_test(self):
        self.hashDeleteHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_files(self):
        tst = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.testuser)
        self.subSetReferenceHelper(tst.add_files, tst.rem_files, tst.list_files, self.files)
        tst.delete()

    def test_reporters(self):
        tst = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.testuser)
        self.subSetReferenceHelper(tst.add_reporters, tst.rem_reporters,
                                   tst.list_reporters, self.reporters)
        tst.delete()


class SubmissionTestCase(test_common_backend.SubMixin,
                         test_common_backend.UUIDHashMixin,
                         StructsTestCase):

    def setUp(self):

        # Call Parent
        super(SubmissionTestCase, self).setUp()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.testuser)

        # Create Files
        file_key = "test"
        file_name = "test1.txt"
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        file_stream = open(file_path, 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_stream,
                                                       filename=file_name,
                                                       name=file_key)
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, file_obj=file_obj, owner=self.testuser).uuid))
        file_obj.close()

    def tearDown(self):

        # Delete Files
        for fle_uuid in self.files:
            fle = self.srv.get_file(fle_uuid)
            fle.delete()

        # Call Parent
        super(SubmissionTestCase, self).tearDown()

    def test_create_submission(self):
        self.hashCreateHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_get_submission(self):
        self.hashGetHelper(self.asn.create_submission,
                           self.srv.get_submission,
                           test_common.SUBMISSION_TESTDICT,
                           extra_kwargs={'owner': self.testuser})

    def test_update_submission(self):
        self.hashUpdateHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_delete_submission(self):
        self.hashDeleteHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT,
                              extra_kwargs={'owner': self.testuser})

    def test_files(self):
        sub = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.testuser)
        self.subSetReferenceHelper(sub.add_files, sub.rem_files, sub.list_files, self.files)
        sub.delete()


class RunTestCaseBaseMixin(object):

    def _test_execute_run_sub(self, submission_file, file_name=None, file_key=None):

        # Proces Input
        if file_name is None:
            file_name = submission_file
        if file_key is None:
            file_key = "submission"

        # Setup Submission File
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, submission_file)
        file_bse = open(file_path, 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse,
                                                       filename=file_name,
                                                       name=file_key)
        data = copy.copy(test_common.FILE_TESTDICT)
        fle_submission = self.srv.create_file(data, file_obj=file_obj, owner=self.student)
        file_obj.close()
        self.sub.add_files([str(fle_submission.uuid)])

        # Run Submission
        data = copy.copy(test_common.RUN_TESTDICT)
        data['test'] = str(self.tst.uuid)
        run = self.sub.execute_run(data, workers=self.workers, owner=self.testuser)
        self.assertTrue(run)
        while not run.is_complete():
            time.sleep(1)
        out = run.get_dict()

        # Cleanup
        run.delete()
        fle_submission.delete()

        # Return
        return out


class RunTestCaseAddTestsMixin(RunTestCaseBaseMixin):

    def test_execute_run_sub_good(self):

        out = self._test_execute_run_sub("add_good.py", file_name="add.py")
        try:
            self.assertEqual(out['status'], self.status_ok)
            if self.retcode_ok:
                self.assertEqual(int(out['retcode']), self.retcode_ok)
            else:
                self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 10)
        except AssertionError as e:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_sub_bad(self):

        out = self._test_execute_run_sub("add_bad.py", file_name="add.py")
        try:
            self.assertEqual(out['status'], self.status_ok)
            if self.retcode_ok:
                self.assertEqual(int(out['retcode']), self.retcode_ok)
            else:
                self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertLess(float(out['score']), 10)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_sub_null(self):

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], self.status_error)
            if self.retcode_error is not None:
                self.assertEqual(int(out['retcode']), self.retcode_error)
            else:
                self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_sub_hang(self):

        out = self._test_execute_run_sub("pgm_hang.py", file_name="add.py")
        try:
            self.assertEqual(out['status'], self.status_error)
            if self.retcode_error is not None:
                self.assertEqual(int(out['retcode']), self.retcode_error)
            else:
                self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_sub_busy(self):

        out = self._test_execute_run_sub("pgm_busy.py", file_name="add.py")
        try:
            self.assertEqual(out['status'], self.status_error)
            if self.retcode_error is not None:
                self.assertEqual(int(out['retcode']), self.retcode_error)
            else:
                self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_sub_forkbomb(self):

        out = self._test_execute_run_sub("pgm_forkbomb.py", file_name="add.py")
        try:
            self.assertEqual(out['status'], self.status_error)
            if self.retcode_error is not None:
                self.assertEqual(int(out['retcode']), self.retcode_error)
            else:
                self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseScriptBase(StructsTestCase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptBase, self).setUp()
        self.admin = self.testuser

        # Setup Assignment
        data = copy.copy(test_common.ASSIGNMENT_TESTDICT)
        self.asn = self.srv.create_assignment(data, owner=self.admin)

        # Setup Test
        data = copy.copy(test_common.TEST_TESTDICT)
        data['tester'] = "script"
        self.tst = self.asn.create_test(data, owner=self.admin)

        # Setup Reporter
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['asn_id'] = test_common.REPMOD_MOODLE_ASN
        self.rpt_moodle = self.srv.create_reporter(data, owner=self.admin)
        self.tst.add_reporters([str(self.rpt_moodle.uuid)])

        # Create Submission User
        self.student = self.auth.create_user(test_common.USER_TESTDICT,
                                             username=test_common.AUTHMOD_MOODLE_STUDENT_USERNAME,
                                             password=test_common.AUTHMOD_MOODLE_STUDENT_PASSWORD,
                                             authmod="moodle")

        # Create Submissions
        self.sub = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.student)

    def tearDown(self):

        # Cleanup
        self.sub.delete()
        self.student.delete()
        self.rpt_moodle.delete()
        self.tst.delete()
        self.asn.delete()

        # Call Parent
        super(RunTestCaseScriptBase, self).tearDown()

    def _setup(self, script_file, file_name=None, file_key=None):

        # Proces Input
        if file_name is None:
            file_name = script_file
        if file_key is None:
            file_key = "script"

        # Setup Test Script
        file_bse = open("{:s}/{:s}".format(test_common.TEST_INPUT_PATH, script_file), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse,
                                                       filename=file_name,
                                                       name=file_key)
        data = copy.copy(test_common.FILE_TESTDICT)
        self.fle_script = self.srv.create_file(data, file_obj=file_obj, owner=self.admin)
        file_obj.close()
        self.tst.add_files([str(self.fle_script.uuid)])

    def _teardown(self):

        # Cleanup Structs
        self.fle_script.delete()


class RunTestCaseBadScriptMixin(RunTestCaseBaseMixin):

    def test_execute_run_script_none(self):

        self.tst.rem_files([str(self.fle_script.uuid)])

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-exception-run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_hidden(self):

        self.fle_script['key'] = ""
        self.tst['path_script'] = ""

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-exception-run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_null(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self.tst.rem_files([str(self.fle_script.uuid)])
        self._teardown()

        # Add New Script
        self._setup("null", file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_hang(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self.tst.rem_files([str(self.fle_script.uuid)])
        self._teardown()

        # Add New Script
        self._setup("pgm_hang.py", file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_busy(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self.tst.rem_files([str(self.fle_script.uuid)])
        self._teardown()

        # Add New Script
        self._setup("pgm_busy.py", file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_forkbomb(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self.tst.rem_files([str(self.fle_script.uuid)])
        self._teardown()

        # Add New Script
        self._setup("pgm_forkbomb.py", file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseScriptArgsKey(RunTestCaseBadScriptMixin,
                               RunTestCaseAddTestsMixin,
                               RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptArgsKey, self).setUp()

        # Call Helper
        self._setup("grade_add_args.py", file_key="script")
        self.tst['path_script'] = ""

    def tearDown(self):

        # Call Helper
        self._teardown()

        # Call Parent
        super(RunTestCaseScriptArgsKey, self).tearDown()


class RunTestCaseScriptStdinKey(RunTestCaseBadScriptMixin,
                                RunTestCaseAddTestsMixin,
                                RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptStdinKey, self).setUp()

        # Call Helper
        self._setup("grade_add_stdin.py", file_key="script")
        self.tst['path_script'] = ""

    def tearDown(self):

        # Call Helper
        self._teardown()

        # Call Parent
        super(RunTestCaseScriptStdinKey, self).tearDown()


class RunTestCaseScriptArgsPath(RunTestCaseBadScriptMixin,
                                RunTestCaseAddTestsMixin,
                                RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptArgsPath, self).setUp()

        # Call Helper
        self._setup("grade_add_args.py", file_key="")
        self.tst['path_script'] = "grade_add_args.py"

    def tearDown(self):

        # Call Helper
        self._teardown()

        # Call Parent
        super(RunTestCaseScriptArgsPath, self).tearDown()


class RunTestCaseScriptStdinPath(RunTestCaseBadScriptMixin,
                                 RunTestCaseAddTestsMixin,
                                 RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptStdinPath, self).setUp()

        # Call Helper
        self._setup("grade_add_stdin.py", file_key="")
        self.tst['path_script'] = "grade_add_stdin.py"

    def tearDown(self):

        # Call Helper
        self._teardown()

        # Call Parent
        super(RunTestCaseScriptStdinPath, self).tearDown()


class RunTestCaseIOBase(StructsTestCase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOBase, self).setUp()
        self.admin = self.testuser

        # Setup Assignment
        data = copy.copy(test_common.ASSIGNMENT_TESTDICT)
        self.asn = self.srv.create_assignment(data, owner=self.admin)

        # Setup Test
        data = copy.copy(test_common.TEST_TESTDICT)
        data['tester'] = "io"
        self.tst = self.asn.create_test(data, owner=self.admin)

        # Setup Reporter
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['asn_id'] = test_common.REPMOD_MOODLE_ASN
        self.rpt_moodle = self.srv.create_reporter(data, owner=self.admin)
        self.tst.add_reporters([str(self.rpt_moodle.uuid)])

        # Create Submission User
        self.student = self.auth.create_user(test_common.USER_TESTDICT,
                                             username=test_common.AUTHMOD_MOODLE_STUDENT_USERNAME,
                                             password=test_common.AUTHMOD_MOODLE_STUDENT_PASSWORD,
                                             authmod="moodle")

        # Create Submissions
        self.sub = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.student)

        # Set Check Values
        self.status_ok = "complete"
        self.retcode_ok = 0
        self.status_error = "complete"
        self.retcode_error = 0

    def tearDown(self):

        # Cleanup
        self.sub.delete()
        self.student.delete()
        self.rpt_moodle.delete()
        self.tst.delete()
        self.asn.delete()

        # Call Parent
        super(RunTestCaseIOBase, self).tearDown()

    def _add_test_file(self, test_file, file_name=None, file_key=None):

        # Proces Input
        if file_name is None:
            file_name = test_file
        if file_key is None:
            file_key = ""

        # Setup Test File
        file_bse = open("{:s}/{:s}".format(test_common.TEST_INPUT_PATH, test_file), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse,
                                                       filename=file_name,
                                                       name=file_key)
        data = copy.copy(test_common.FILE_TESTDICT)
        fle = self.srv.create_file(data, file_obj=file_obj, owner=self.admin)
        file_obj.close()
        self.tst.add_files([str(fle.uuid)])

        return fle

    def _del_test_file(self, fle):

        # Cleanup Test File
        self.tst.rem_files([str(fle.uuid)])
        fle.delete()


class RunTestCaseBadSolnMixin(RunTestCaseBaseMixin):

    def test_execute_run_solution_none(self):

        self.tst.rem_files([str(self.fle_solution.uuid)])

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-exception-run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_hidden(self):

        self.fle_solution['key'] = ""
        self.tst['path_solution'] = ""

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-exception-run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_null(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_file(self.fle_solution)

        # Add New Solution
        self.fle_solution = self._add_test_file("null",
                                                file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete")
            self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 10)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_hang(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_file(self.fle_solution)

        # Add New Solution
        self.fle_solution = self._add_test_file("pgm_hang.py",
                                                file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_busy(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_file(self.fle_solution)

        # Add New Solution
        self.fle_solution = self._add_test_file("pgm_busy.py",
                                                file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_forkbomb(self):

        # Extract Data and Remove Original Script
        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_file(self.fle_solution)

        # Add New Solution
        self.fle_solution = self._add_test_file("pgm_forkbomb.py",
                                                file_name=file_name, file_key=file_key)

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseBadInputMixin(RunTestCaseBaseMixin):

    def test_execute_run_input_none(self):

        self.tst.rem_files([str(self.fle_input1.uuid)])
        self.tst.rem_files([str(self.fle_input2.uuid)])
        self.tst.rem_files([str(self.fle_input3.uuid)])

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_input_hidden(self):

        self.tst['prefix_input'] = ""
        self.fle_input1['key'] = ""
        self.fle_input2['key'] = ""
        self.fle_input3['key'] = ""

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_input_null(self):

        file_name = self.fle_input1['name']
        file_key = self.fle_input1['key']
        self._del_test_file(self.fle_input1)
        self.fle_input1 = self._add_test_file("null", file_key="input")

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseIOKeyAdd(RunTestCaseBadSolnMixin,
                          RunTestCaseBadInputMixin,
                          RunTestCaseAddTestsMixin,
                          RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOKeyAdd, self).setUp()

        # Add Solution
        self.tst['path_solution'] = ""
        self.fle_solution = self._add_test_file("add_good.py", file_key="solution")

        # Add Test Inputs
        self.tst['prefix_input'] = ""
        self.fle_input1 = self._add_test_file("add_input1.txt",
                                              file_name="input1.txt", file_key="input")
        self.fle_input2 = self._add_test_file("add_input2.txt",
                                              file_name="input2.txt", file_key="input")
        self.fle_input3 = self._add_test_file("add_input3.txt",
                                              file_name="input3.txt", file_key="input")

    def tearDown(self):

        # Remove Solution
        self._del_test_file(self.fle_input3)
        self._del_test_file(self.fle_input2)
        self._del_test_file(self.fle_input1)
        self._del_test_file(self.fle_solution)

        # Call Parent
        super(RunTestCaseIOKeyAdd, self).tearDown()


# Main
if __name__ == '__main__':
    unittest.main()
