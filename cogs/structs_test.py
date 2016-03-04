#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest
import os
import time
import random
import zipfile
import shutil

import test_common
import test_common_backend

import auth
import structs
import repmod_moodle

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

    def _copy_test_file(self, input_name, output_name):
        src = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, input_name)
        dst = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, output_name)
        shutil.copy(src, dst)

class ServerTestCase(test_common_backend.SubMixin,
                     StructsTestCase):

    def setUp(self):
        super(ServerTestCase, self).setUp()

    def tearDown(self):
        super(ServerTestCase, self).tearDown()

    def test_files(self):
        data = copy.copy(test_common.FILE_TESTDICT)
        file_name = "test1.txt"
        src_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        self.subHashDirectHelper(self.srv.create_file,
                                 self.srv.get_file,
                                 self.srv.list_files,
                                 data,
                                 extra_kwargs={'src_path': src_path, 'owner': self.testuser})

    def test_reporters(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
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

        # Setup Data
        self.data = copy.copy(test_common.FILE_TESTDICT)

        # Setup Test File
        file_key = "test"
        file_name = "test1.txt"
        self.src_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)

    def tearDown(self):

        # Call Parent
        super(FileTestCase, self).tearDown()

    def test_create_file(self):
        self.hashCreateHelper(self.srv.create_file,
                              self.data,
                              extra_kwargs={'src_path': self.src_path, 'owner': self.testuser})

    def test_get_file(self):
        self.hashGetHelper(self.srv.create_file,
                           self.srv.get_file,
                           self.data,
                           extra_kwargs={'src_path': self.src_path, 'owner': self.testuser})

    def test_update_file(self):
        self.hashUpdateHelper(self.srv.create_file,
                              self.data,
                              extra_kwargs={'src_path': self.src_path, 'owner': self.testuser})

    def test_delete_file(self):
        self.hashDeleteHelper(self.srv.create_file,
                              self.data,
                              extra_kwargs={'src_path': self.src_path, 'owner': self.testuser})

    def _run_zip_test(self, file_names):

        # Process Input
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
            data = copy.copy(test_common.FILE_TESTDICT)
            data['key'] = "extract"
            data['name'] = archive_name

            # Create from Zip
            fles = self.srv.create_files(data, archive_src_path=archive_path, owner=self.testuser)

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

    def test_file_report_moodle_nodue_asnid(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_NODUE
        data['moodle_only_higher'] = "0"
        grade = (random.randint(0, 1000) / 100.0)
        comments = "Tested via test_file_report_moodle_nodue_asnid on {:s}.".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, grade, comments)
        self.assertEqual(grade, grade_out)
        reporter.delete()

    def test_file_report_moodle_nodue_cmid(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_cm_id'] = test_common.REPMOD_MOODLE_CM_NODUE
        data['moodle_only_higher'] = "0"
        grade = (random.randint(0, 1000) / 100.0)
        comments = "Tested via test_file_report_moodle_nodue_cmid on {:s}.".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, grade, comments)
        self.assertEqual(grade, grade_out)
        reporter.delete()

    def test_file_report_moodle_pastdue_nocut(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_PASTDUE
        data['moodle_respect_duedate'] = "1"
        data['moodle_late_penalty'] = "0"
        data['moodle_late_period'] = "0"
        data['moodle_only_higher'] = "0"
        grade = 5.0
        comments = "Tested via test_file_report_moodle_pastdue_nocut "
        comments += "on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, grade, comments)
        self.assertEqual(0, grade_out)
        reporter.delete()

    def test_file_report_moodle_pastcut(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_PASTCUT
        data['moodle_respect_duedate'] = "1"
        data['moodle_late_penalty'] = "0"
        data['moodle_late_period'] = "0"
        data['moodle_only_higher'] = "0"
        grade = 5.0
        comments = "Tested via test_file_report_moodle_pastcut "
        comments += "on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, grade, comments)
        self.assertEqual(0, grade_out)
        reporter.delete()

    def test_file_report_moodle_late(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_LATE
        data['moodle_respect_duedate'] = "1"
        data['moodle_late_penalty'] = "5"
        data['moodle_late_period'] = "548640000" # 10 years - good through 2025
        data['moodle_only_higher'] = "0"
        grade = 10.0
        comments = "Tested via test_file_report_moodle_late "
        comments += "on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, grade, comments)
        self.assertEqual(5, grade_out)
        reporter.delete()

    def test_file_report_moodle_pastdue_ignore(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_PASTDUE
        data['moodle_respect_duedate'] = "0"
        data['moodle_only_higher'] = "0"
        grade = 5.0
        comments = "Tested via test_file_report_moodle_pastdue on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, grade, comments)
        self.assertEqual(grade, grade_out)
        reporter.delete()

    def test_file_report_moodle_prereq(self):

        prereq = copy.copy(test_common.REPORTER_TESTDICT)
        prereq['mod'] = "moodle"
        prereq['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_NODUE
        prereq['moodle_respect_duedate'] = "0"
        prereq['moodle_only_higher'] = "0"

        newasn = copy.copy(test_common.REPORTER_TESTDICT)
        newasn['mod'] = "moodle"
        newasn['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_HIGHER
        newasn['moodle_respect_duedate'] = "0"
        newasn['moodle_only_higher'] = "0"
        newasn['moodle_prereq_asn_id'] = test_common.REPMOD_MOODLE_ASN_NODUE
        newasn['moodle_prereq_min'] = "5"

        # Setup Pass
        prereq_grade = 7.0
        comments = "Tested via test_file_report_moodle_prereq on {:s} (setpreq).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(prereq_grade)
        reporter = self.srv.create_reporter(prereq, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, prereq_grade, comments)
        try:
            self.assertEqual(prereq_grade, grade_out)
        except AssertionError as e:
            print(extra_out)
        reporter.delete()

        # Test Pass
        new_grade = 10.0
        comments = "Tested via test_file_report_moodle_prereq on {:s} (pass).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(new_grade)
        reporter = self.srv.create_reporter(newasn, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, new_grade, comments)
        try:
            self.assertEqual(new_grade, grade_out)
        except AssertionError as e:
            print(extra_out)
        reporter.delete()

        # Setup Fail
        prereq_grade = 3.0
        comments = "Tested via test_file_report_moodle_prereq on {:s} (setpreq).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(prereq_grade)
        reporter = self.srv.create_reporter(prereq, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, prereq_grade, comments)
        try:
            self.assertEqual(prereq_grade, grade_out)
        except AssertionError as e:
            print(extra_out)
        reporter.delete()

        # Test Fail
        new_grade = 10.0
        comments = "Tested via test_file_report_moodle_prereq on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(new_grade)
        reporter = self.srv.create_reporter(newasn, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN", self.student, new_grade, comments)
        try:
            self.assertEqual(0, grade_out)
        except AssertionError as e:
            print(extra_out)
        reporter.delete()

    def test_file_report_moodle_higher(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_HIGHER
        data['moodle_respect_duedate'] = "0"
        data['moodle_only_higher'] = "1"
        grade = 10.0
        comments = "Tested via test_file_report_moodle_higher on {:s} (pass).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN",self.student, grade, comments)
        self.assertEqual(grade, grade_out)
        grade = 5.0
        comments = "Tested via test_file_report_moodle_higher on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN",self.student, grade, comments)
        self.assertEqual(grade, grade_out)
        reporter.delete()

    def test_file_report_moodle_higher_ignore(self):
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_HIGHER
        data['moodle_respect_duedate'] = "0"
        data['moodle_only_higher'] = "0"
        grade = 10.0
        comments = "Tested via test_file_report_moodle_higher on {:s} (pass).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN",self.student, grade, comments)
        self.assertEqual(grade, grade_out)
        grade = 5.0
        comments = "Tested via test_file_report_moodle_higher on {:s} (fail).".format(time.asctime())
        comments += "\nGrade = {:.2f}".format(grade)
        reporter = self.srv.create_reporter(data, owner=self.testuser)
        grade_out, extra_out = reporter.file_report("FAKE_RUN",self.student, grade, comments)
        self.assertEqual(grade, grade_out)
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
        file_name = "test1.txt"
        src_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, src_path=src_path, owner=self.testuser).uuid))

        # Create Reporters
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_NODUE
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
        src_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, src_path=src_path, owner=self.testuser).uuid))

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
            file_key = ""

        # Setup Submission File
        src_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, submission_file)
        data = copy.copy(test_common.FILE_TESTDICT)
        data['name'] = file_name
        data['key'] = file_key
        if file_key == "extract":
            fles = self.srv.create_files(data, archive_src_path=src_path, owner=self.admin)
        else:
            fles = [self.srv.create_file(data, src_path=src_path, owner=self.student)]
        uuids = [str(fle.uuid) for fle in fles]
        self.sub.add_files(uuids)

        # Run Submission
        data = copy.copy(test_common.RUN_TESTDICT)
        data['test'] = str(self.tst.uuid)
        run = self.sub.execute_run(data, owner=self.testuser)
        self.assertTrue(run)
        while not run.is_complete():
            time.sleep(1)
        out = run.get_dict()

        # Cleanup
        run.delete()
        for fle in fles:
            fle.delete()

        # Return
        return out


class RunTestCaseBadTestsMixin(RunTestCaseBaseMixin):

    def test_execute_run_sub_none(self):

        # Run Submission
        data = copy.copy(test_common.RUN_TESTDICT)
        data['test'] = str(self.tst.uuid)
        run = self.sub.execute_run(data, owner=self.testuser)
        self.assertTrue(run)
        while not run.is_complete():
            time.sleep(1)
        out = run.get_dict()

        # Cleanup
        run.delete()

        # Check Output
        try:
            self.assertEqual(out['status'], self.status_nosub)
            if self.retcode_nosub is not None:
                self.assertEqual(int(out['retcode']), self.retcode_nosub)
            else:
                self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_sub_null(self):

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
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

        out = self._test_execute_run_sub("pgm_hang.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
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

        out = self._test_execute_run_sub("pgm_busy.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
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

        out = self._test_execute_run_sub("pgm_forkbomb.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
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


class RunTestCaseAddTestsMixin(RunTestCaseBaseMixin):

    def test_execute_run_sub_good(self):

        out = self._test_execute_run_sub("add_good.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
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

        out = self._test_execute_run_sub("add_bad.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
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


class RunTestCaseAddTestsZipMixin(RunTestCaseBaseMixin):

    def test_execute_run_sub_zip_good(self):

        # Setup Zip
        self._copy_test_file("add_good.py", self.sub_name)
        file_name = self.sub_name
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "submission.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Zip
        out = self._test_execute_run_sub(archive_name, file_key="extract")

        # Remove Zip and Copy
        os.remove(archive_path)
        os.remove(file_path)

        # Check Output
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

    def test_execute_run_sub_zip_bad(self):

        # Setup Zip
        self._copy_test_file("add_bad.py", self.sub_name)
        file_name = self.sub_name
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "submission.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Zip
        out = self._test_execute_run_sub(archive_name, file_key="extract")

        # Remove Zip and Copy
        os.remove(archive_path)
        os.remove(file_path)

        # Check Output
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


class RunTestCaseHelloTestsMixin(RunTestCaseBaseMixin):

    def test_execute_run_sub_good(self):

        out = self._test_execute_run_sub("hello_good.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
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

        out = self._test_execute_run_sub("hello_bad.py",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], self.status_ok)
            if self.retcode_ok:
                self.assertEqual(int(out['retcode']), self.retcode_ok)
            else:
                self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseHelloTestsZipMixin(RunTestCaseBaseMixin):

    def test_execute_run_sub_good_zip(self):

        # Setup Zip
        self._copy_test_file("hello_good.py", self.sub_name)
        file_name = self.sub_name
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "submission.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Zip
        out = self._test_execute_run_sub(archive_name, file_key="extract")

        # Remove Zip and Copy
        os.remove(archive_path)
        os.remove(file_path)

        # Check Output
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

    def test_execute_run_sub_bad_zip(self):

        # Setup Zip
        self._copy_test_file("hello_bad.py", self.sub_name)
        file_name = self.sub_name
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "submission.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Zip
        out = self._test_execute_run_sub(archive_name, file_key="extract")

        # Remove Zip and Copy
        os.remove(archive_path)
        os.remove(file_path)

        # Check Output
        try:
            self.assertEqual(out['status'], self.status_ok)
            if self.retcode_ok:
                self.assertEqual(int(out['retcode']), self.retcode_ok)
            else:
                self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseBadScriptMixin(RunTestCaseBaseMixin):

    def test_execute_run_script_none(self):

        self.tst.rem_files([str(self.fle_script.uuid)])

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-exception-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_hidden(self):

        self.fle_script['key'] = ""
        self.tst['path_script'] = ""

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_null(self):

        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self._del_test_files([self.fle_script])
        fles = self._add_test_files("null", file_name=file_name, file_key=file_key)
        self.fle_script = fles[0]

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_hang(self):

        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self._del_test_files([self.fle_script])
        fles = self._add_test_files("pgm_hang.py", file_name=file_name, file_key=file_key)
        self.fle_script = fles[0]

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_busy(self):

        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self._del_test_files([self.fle_script])
        fles = self._add_test_files("pgm_busy.py", file_name=file_name, file_key=file_key)
        self.fle_script = fles[0]

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_script_forkbomb(self):

        file_name = self.fle_script['name']
        file_key = self.fle_script['key']
        self._del_test_files([self.fle_script])
        fles = self._add_test_files("pgm_forkbomb.py", file_name=file_name, file_key=file_key)
        self.fle_script = fles[0]

        out = self._test_execute_run_sub("null", file_name="add.py")
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseBadSolnMixin(RunTestCaseBaseMixin):

    def test_execute_run_solution_none(self):

        self.tst.rem_files([str(self.fle_solution.uuid)])

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-exception-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_hidden(self):

        self.fle_solution['key'] = ""
        self.tst['path_solution'] = ""

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-exception-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_null(self):

        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_files([self.fle_solution])
        fles = self._add_test_files("null", file_name=file_name, file_key=file_key)
        self.fle_solution = fles[0]

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete")
            self.assertEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 10)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_hang(self):

        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_files([self.fle_solution])
        fles = self._add_test_files("pgm_hang.py", file_name=file_name, file_key=file_key)
        self.fle_solution = fles[0]

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_busy(self):

        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_files([self.fle_solution])
        fles = self._add_test_files("pgm_busy.py", file_name=file_name, file_key=file_key)
        self.fle_solution = fles[0]

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_solution_forkbomb(self):

        file_name = self.fle_solution['name']
        file_key = self.fle_solution['key']
        self._del_test_files([self.fle_solution])
        fles = self._add_test_files("pgm_forkbomb.py", file_name=file_name, file_key=file_key)
        self.fle_solution = fles[0]

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
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

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
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

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise

    def test_execute_run_input_null(self):

        #pylint: disable=access-member-before-definition
        file_name = self.fle_input1['name']
        file_key = self.fle_input1['key']
        self._del_test_files([self.fle_input1])
        fles = self._add_test_files("null", file_name=file_name, file_key=file_key)
        self.fle_input1 = fles[0]

        out = self._test_execute_run_sub("null",
                                         file_name=self.sub_name, file_key=self.sub_key)
        try:
            self.assertEqual(out['status'], "complete-error-tester_run")
            self.assertNotEqual(int(out['retcode']), 0)
            self.assertTrue(out['output'])
            self.assertEqual(float(out['score']), 0)
        except AssertionError:
            print("run = {:s}".format(out))
            raise


class RunTestCaseBase(StructsTestCase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseBase, self).setUp()
        self.admin = self.testuser

        # Setup Assignment
        data = copy.copy(test_common.ASSIGNMENT_TESTDICT)
        self.asn = self.srv.create_assignment(data, owner=self.admin)

        # Setup Reporter
        data = copy.copy(test_common.REPORTER_TESTDICT)
        data['mod'] = "moodle"
        data['moodle_asn_id'] = test_common.REPMOD_MOODLE_ASN_NODUE
        self.rpt_moodle = self.srv.create_reporter(data, owner=self.admin)

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
        self.asn.delete()

        # Call Parent
        super(RunTestCaseBase, self).tearDown()

    def _setup_test(self, mod_tester):
        data = copy.copy(test_common.TEST_TESTDICT)
        data['tester'] = mod_tester
        self.tst = self.asn.create_test(data, owner=self.admin)
        self.tst.add_reporters([str(self.rpt_moodle.uuid)])

    def _teardown_test(self):
        self.tst.delete()

    def _add_test_files(self, test_file, file_name=None, file_key=None):

        # Proces Input
        if file_name is None:
            file_name = test_file
        if file_key is None:
            file_key = ""

        # Setup Test Files
        src_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, test_file)
        data = copy.copy(test_common.FILE_TESTDICT)
        data['name'] = file_name
        data['key'] = file_key
        if file_key == "extract":
            fles = self.srv.create_files(data, archive_src_path=src_path, owner=self.admin)
        else:
            fles = [self.srv.create_file(data, src_path=src_path, owner=self.admin)]
        uuids = [str(fle.uuid) for fle in fles]
        self.tst.add_files(uuids)

        return fles

    def _del_test_files(self, fles):

        # Cleanup Test Files
        for fle in fles:
            self.tst.rem_files([str(fle.uuid)])
            fle.delete()


class RunTestCaseScriptBase(RunTestCaseBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptBase, self).setUp()

        # Setup Test
        self._setup_test("script")

        # Set Mixin Values
        self.status_ok = "complete"
        self.retcode_ok = 0
        self.status_error = "complete-error-tester_run"
        self.retcode_error = None
        self.status_nosub = "complete"
        self.retcode_nosub = 0

    def tearDown(self):

        # Cleanup
        self._teardown_test()

        # Call Parent
        super(RunTestCaseScriptBase, self).tearDown()


class RunTestCaseScriptArgsKey(RunTestCaseBadScriptMixin,
                               RunTestCaseAddTestsMixin,
                               RunTestCaseBadTestsMixin,
                               RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptArgsKey, self).setUp()

        # Add Script File
        fles = self._add_test_files("grade_add_args.py", file_key="script")
        self.fle_script = fles[0]
        self.tst['path_script'] = ""

        # Set Mixin Values
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Script File
        self._del_test_files([self.fle_script])

        # Call Parent
        super(RunTestCaseScriptArgsKey, self).tearDown()


class RunTestCaseScriptStdinKey(RunTestCaseAddTestsMixin,
                                RunTestCaseBadTestsMixin,
                                RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptStdinKey, self).setUp()

        # Add Script File
        fles = self._add_test_files("grade_add_stdin.py", file_key="script")
        self.fle_script = fles[0]
        self.tst['path_script'] = ""

        # Set Mixin Values
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Script File
        self._del_test_files([self.fle_script])

        # Call Parent
        super(RunTestCaseScriptStdinKey, self).tearDown()


class RunTestCaseScriptArgsPath(RunTestCaseBadScriptMixin,
                                RunTestCaseAddTestsMixin,
                                RunTestCaseAddTestsZipMixin,
                                RunTestCaseBadTestsMixin,
                                RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptArgsPath, self).setUp()

        # Add Script File
        self.tst['path_script'] = "grade_add_args.py"
        fles = self._add_test_files(self.tst['path_script'])
        self.fle_script = fles[0]

        # Set Mixin Values
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Script File
        self._del_test_files([self.fle_script])

        # Call Parent
        super(RunTestCaseScriptArgsPath, self).tearDown()


class RunTestCaseScriptArgsPathZip(RunTestCaseAddTestsMixin,
                                   RunTestCaseAddTestsZipMixin,
                                   RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptArgsPathZip, self).setUp()

        # Setup Zip
        self.tst['path_script'] = "grade_add_args.py"
        file_name = self.tst['path_script']
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "tester.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Tester Zip
        self.fles_tester = self._add_test_files(archive_name, file_key="extract")

        # Remove Zip
        os.remove(archive_path)

        # Set Mixin Values
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Files
        self._del_test_files(self.fles_tester)

        # Call Parent
        super(RunTestCaseScriptArgsPathZip, self).tearDown()


class RunTestCaseScriptStdinPath(RunTestCaseAddTestsMixin,
                                 RunTestCaseAddTestsZipMixin,
                                 RunTestCaseBadTestsMixin,
                                 RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptStdinPath, self).setUp()

        # Add Script File
        self.tst['path_script'] = "grade_add_stdin.py"
        fles = self._add_test_files(self.tst['path_script'])
        self.fle_script = fles[0]

        # Set Mixin Values
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Script File
        self._del_test_files([self.fle_script])

        # Call Parent
        super(RunTestCaseScriptStdinPath, self).tearDown()


class RunTestCaseScriptStdinPathZip(RunTestCaseAddTestsMixin,
                                    RunTestCaseAddTestsZipMixin,
                                    RunTestCaseScriptBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScriptStdinPathZip, self).setUp()

        # Setup Zip
        self.tst['path_script'] = "grade_add_stdin.py"
        file_name = self.tst['path_script']
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "tester.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Tester Zip
        self.fles_tester = self._add_test_files(archive_name, file_key="extract")

        # Remove Zip
        os.remove(archive_path)

        # Set Mixin Values
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Files
        self._del_test_files(self.fles_tester)

        # Call Parent
        super(RunTestCaseScriptStdinPathZip, self).tearDown()


class RunTestCaseIOBase(RunTestCaseBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOBase, self).setUp()

        # Setup Test
        self._setup_test("io")

        # Set Mixin Values
        self.status_ok = "complete"
        self.retcode_ok = 0
        self.status_error = "complete"
        self.retcode_error = 0
        self.status_nosub = "complete-exception-tester_run"
        self.retcode_nosub = -1

    def tearDown(self):

        # Cleanup
        self._teardown_test()

        # Call Parent
        super(RunTestCaseIOBase, self).tearDown()


class RunTestCaseIOKeyAdd(RunTestCaseBadSolnMixin,
                          RunTestCaseBadInputMixin,
                          RunTestCaseBadTestsMixin,
                          RunTestCaseAddTestsMixin,
                          RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOKeyAdd, self).setUp()

        # Add Solution
        self.tst['path_solution'] = ""
        fles = self._add_test_files("add_good.py", file_key="solution")
        self.fle_solution = fles[0]

        # Add Test Inputs
        self.tst['prefix_input'] = ""
        fles = self._add_test_files("add_input1.txt", file_name="input1.txt", file_key="input")
        self.fle_input1 = fles[0]
        fles = self._add_test_files("add_input2.txt", file_name="input2.txt", file_key="input")
        self.fle_input2 = fles[0]
        fles = self._add_test_files("add_input3.txt", file_name="input3.txt", file_key="input")
        self.fle_input3 = fles[0]

        # Set Mixin Values
        self.tst['path_submission'] = ""
        self.sub_name = "add.py"
        self.sub_key = "submission"

    def tearDown(self):

        # Remove Solution
        self._del_test_files([self.fle_input3, self.fle_input2, self.fle_input1])
        self._del_test_files([self.fle_solution])

        # Call Parent
        super(RunTestCaseIOKeyAdd, self).tearDown()


class RunTestCaseIOKeyHello(RunTestCaseHelloTestsMixin,
                            RunTestCaseBadTestsMixin,
                            RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOKeyHello, self).setUp()

        # Add Solution
        self.tst['path_solution'] = ""
        fles = self._add_test_files("hello_good.py", file_key="solution")
        self.fle_solution = fles[0]

        # Set Mixin Values
        self.tst['path_submission'] = ""
        self.sub_name = "hello.py"
        self.sub_key = "submission"

    def tearDown(self):

        # Remove Solution
        self._del_test_files([self.fle_solution])

        # Call Parent
        super(RunTestCaseIOKeyHello, self).tearDown()


class RunTestCaseIOPathAdd(RunTestCaseBadSolnMixin,
                           RunTestCaseBadInputMixin,
                           RunTestCaseBadTestsMixin,
                           RunTestCaseAddTestsMixin,
                           RunTestCaseAddTestsZipMixin,
                           RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOPathAdd, self).setUp()

        # Add Solution
        self.tst['path_solution'] = "add_good.py"
        fles = self._add_test_files(self.tst['path_solution'])
        self.fle_solution = fles[0]

        # Add Test Inputs
        self.tst['prefix_input'] = "input"
        fles = self._add_test_files("add_input1.txt", file_name="input1.txt")
        self.fle_input1 = fles[0]
        fles = self._add_test_files("add_input2.txt", file_name="input2.txt")
        self.fle_input2 = fles[0]
        fles = self._add_test_files("add_input3.txt", file_name="input3.txt")
        self.fle_input3 = fles[0]

        # Set Mixin Values
        self.tst['path_submission'] = "add.py"
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Solution
        self._del_test_files([self.fle_input3, self.fle_input2, self.fle_input1])
        self._del_test_files([self.fle_solution])

        # Call Parent
        super(RunTestCaseIOPathAdd, self).tearDown()


class RunTestCaseIOPathAddZip(RunTestCaseBadTestsMixin,
                              RunTestCaseAddTestsMixin,
                              RunTestCaseAddTestsZipMixin,
                              RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOPathAddZip, self).setUp()

        # Setup Files
        self.tst['path_solution'] = "add_good.py"
        self.tst['prefix_input'] = "input"
        self._copy_test_file("add_input1.txt", "input1.txt")
        self._copy_test_file("add_input2.txt", "input2.txt")
        self._copy_test_file("add_input3.txt", "input3.txt")

        # Setup Zip
        file_names = ["add_good.py", "input1.txt", "input2.txt", "input3.txt"]
        file_paths = []
        for file_name in file_names:
            file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
            file_paths.append(file_path)
        archive_name = "tester.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, file_paths)

        # Add Tester Zip
        self.fles_tester = self._add_test_files(archive_name, file_key="extract")

        # Remove Zip and Copies
        os.remove(archive_path)
        for file_name in ["input1.txt", "input2.txt", "input3.txt"]:
            file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
            os.remove(file_path)

        # Set Mixin Values
        self.tst['path_submission'] = "add.py"
        self.sub_name = "add.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Solution
        self._del_test_files(self.fles_tester)

        # Call Parent
        super(RunTestCaseIOPathAddZip, self).tearDown()


class RunTestCaseIOPathHello(RunTestCaseBadTestsMixin,
                             RunTestCaseHelloTestsMixin,
                             RunTestCaseHelloTestsZipMixin,
                             RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOPathHello, self).setUp()

        # Add Solution
        self.tst['path_solution'] = "hello_good.py"
        fles = self._add_test_files(self.tst['path_solution'])
        self.fle_solution = fles[0]

        # Set Mixin Values
        self.tst['path_submission'] = "hello.py"
        self.sub_name = "hello.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Solution
        self._del_test_files([self.fle_solution])

        # Call Parent
        super(RunTestCaseIOPathHello, self).tearDown()


class RunTestCaseIOPathHelloZip(RunTestCaseBadTestsMixin,
                                RunTestCaseHelloTestsMixin,
                                RunTestCaseHelloTestsZipMixin,
                                RunTestCaseIOBase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIOPathHelloZip, self).setUp()

        # Setup Zip
        self.tst['path_solution'] = "hello_good.py"
        file_name = self.tst['path_solution']
        file_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, file_name)
        archive_name = "tester.zip"
        archive_path = "{:s}/{:s}".format(test_common.TEST_INPUT_PATH, archive_name)
        self._create_zip(archive_path, [file_path])

        # Add Tester Zip
        self.fles_tester = self._add_test_files(archive_name, file_key="extract")

        # Remove Zip and Copies
        os.remove(archive_path)

        # Set Mixin Values
        self.tst['path_submission'] = "hello.py"
        self.sub_name = "hello.py"
        self.sub_key = ""

    def tearDown(self):

        # Remove Solution
        self._del_test_files(self.fles_tester)

        # Call Parent
        super(RunTestCaseIOPathHelloZip, self).tearDown()


# Main
if __name__ == '__main__':
    unittest.main()
