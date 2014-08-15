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

import test_common
import test_common_backend

import auth
import structs


_NUM_WORKERS = 10


class StructsTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(StructsTestCase, self).setUp()

        # Setup Auth
        self.auth = auth.Auth()

        # Create User
        self.user = self.auth.create_user(test_common.USER_TESTDICT,
                                          username="testuser",
                                          password="testpass",
                                          authmod="test")

        # Setup Server
        self.srv = structs.Server()

        # Setup Worker Pool
        self.workers = multiprocessing.Pool(_NUM_WORKERS)

    def tearDown(self):

        # Cleanup Pool
        self.workers.close()
        self.workers.join()

        # Cleanup Server
        self.srv.close()

        # Cleanup User
        self.user.delete()

        # Call parent
        super(StructsTestCase, self).tearDown()


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
                                 extra_kwargs={'file_obj': file_obj, 'owner': self.user})
        file_obj.close()

    def test_assignments(self):
        self.subHashDirectHelper(self.srv.create_assignment,
                                 self.srv.get_assignment,
                                 self.srv.list_assignments,
                                 test_common.ASSIGNMENT_TESTDICT,
                                 extra_kwargs={'owner': self.user})

    def test_asn_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 asn.list_tests,
                                 test_common.TEST_TESTDICT,
                                 extra_kwargs={'owner': self.user})
        asn.delete()

    def test_srv_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 self.srv.list_tests,
                                 test_common.TEST_TESTDICT,
                                 extra_kwargs={'owner': self.user})
        asn.delete()

    def test_asn_submissions(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)
        self.subHashDirectHelper(asn.create_submission,
                                 self.srv.get_submission,
                                 asn.list_submissions,
                                 test_common.SUBMISSION_TESTDICT,
                                 extra_kwargs={'owner': self.user})
        asn.delete()

    def test_srv_submissions(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)
        self.subHashDirectHelper(asn.create_submission,
                                 self.srv.get_submission,
                                 self.srv.list_submissions,
                                 test_common.SUBMISSION_TESTDICT,
                                 extra_kwargs={'owner': self.user})
        asn.delete()


class FileTestCase(test_common_backend.UUIDHashMixin,
                   StructsTestCase):

    def setUp(self):
        super(FileTestCase, self).setUp()
        src_file = open("./Makefile", 'rb')
        self.file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")

    def tearDown(self):
        self.file_obj.close()
        super(FileTestCase, self).tearDown()

    def test_create_file(self):
        self.hashCreateHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.user})

    def test_get_file(self):
        self.hashGetHelper(self.srv.create_file,
                           self.srv.get_file,
                           test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.user})

    def test_update_file(self):
        self.hashUpdateHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.user})

    def test_delete_file(self):
        self.hashDeleteHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj, 'owner': self.user})


class AssignmentTestCase(test_common_backend.UUIDHashMixin,
                         StructsTestCase):

    def setUp(self):
        super(AssignmentTestCase, self).setUp()

    def tearDown(self):
        super(AssignmentTestCase, self).tearDown()

    def test_create_assignment(self):
        self.hashCreateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_get_assignment(self):
        self.hashGetHelper(self.srv.create_assignment,
                           self.srv.get_assignment,
                           test_common.ASSIGNMENT_TESTDICT,
                           extra_kwargs={'owner': self.user})

    def test_update_assignment(self):
        self.hashUpdateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_delete_assignment(self):
        self.hashDeleteHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              extra_kwargs={'owner': self.user})


class TestTestCase(test_common_backend.SubMixin,
                   test_common_backend.UUIDHashMixin,
                   StructsTestCase):

    def setUp(self):

        # Call Parent
        super(TestTestCase, self).setUp()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)

        # Create Files
        src_file = open("./Makefile", 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, file_obj=file_obj, owner=self.user).uuid))
        file_obj.close()

    def tearDown(self):

        # Delete Files
        for fle_uuid in self.files:
            fle = self.srv.get_file(fle_uuid)
            fle.delete()

        # Call Parent
        super(TestTestCase, self).tearDown()

    def test_create_test(self):
        self.hashCreateHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_get_test(self):
        self.hashGetHelper(self.asn.create_test,
                           self.srv.get_test,
                           test_common.TEST_TESTDICT,
                           extra_kwargs={'owner': self.user})

    def test_update_test(self):
        self.hashUpdateHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_delete_test(self):
        self.hashDeleteHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_files(self):
        tst = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.user)
        self.subSetReferenceHelper(tst.add_files, tst.rem_files, tst.list_files, self.files)
        tst.delete()


class SubmissionTestCase(test_common_backend.SubMixin,
                         test_common_backend.UUIDHashMixin,
                         StructsTestCase):

    def setUp(self):

        # Call Parent
        super(SubmissionTestCase, self).setUp()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)

        # Create Files
        src_file = open("./Makefile", 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, file_obj=file_obj, owner=self.user).uuid))
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
                              extra_kwargs={'owner': self.user})

    def test_get_submission(self):
        self.hashGetHelper(self.asn.create_submission,
                           self.srv.get_submission,
                           test_common.SUBMISSION_TESTDICT,
                           extra_kwargs={'owner': self.user})

    def test_update_submission(self):
        self.hashUpdateHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_delete_submission(self):
        self.hashDeleteHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT,
                              extra_kwargs={'owner': self.user})

    def test_files(self):
        sub = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.user)
        self.subSetReferenceHelper(sub.add_files, sub.rem_files, sub.list_files, self.files)
        sub.delete()


class RunTestCaseScript(test_common_backend.SubMixin,
                        test_common_backend.UUIDHashMixin,
                        StructsTestCase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseScript, self).setUp()

        # Create Args Test Script
        file_bse = open("{:s}/grade_add_args.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="grade.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.tst_file_args = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Stdin Test Script
        file_bse = open("{:s}/grade_add_stdin.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="grade.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.tst_file_stdin = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Hanging Script
        file_bse = open("{:s}/pgm_hang.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="pgm.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.pgm_hang = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Busy Script
        file_bse = open("{:s}/pgm_busy.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="pgm.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.pgm_busy = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Forkbomb Script
        file_bse = open("{:s}/pgm_forkbomb.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="pgm.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.pgm_fork = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Good Sub File
        file_bse = open("{:s}/add_good.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="add.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'submission'
        self.sub_file_good = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Bad Sub File
        file_bse = open("{:s}/add_bad.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="add.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'submission'
        self.sub_file_bad = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)

        # Create Tests
        self.tst_args = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.user)
        self.tst_args.add_files([str(self.tst_file_args.uuid)])
        self.tst_stdin = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.user)
        self.tst_stdin.add_files([str(self.tst_file_stdin.uuid)])
        self.tst_hang = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.user)
        self.tst_hang.add_files([str(self.pgm_hang.uuid)])
        self.tst_busy = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.user)
        self.tst_busy.add_files([str(self.pgm_busy.uuid)])
        self.tst_fork = self.asn.create_test(test_common.TEST_TESTDICT, owner=self.user)
        self.tst_fork.add_files([str(self.pgm_fork.uuid)])

        # Create Submissions
        self.sub_good = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.user)
        self.sub_good.add_files([str(self.sub_file_good.uuid)])
        self.sub_bad = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.user)
        self.sub_bad.add_files([str(self.sub_file_bad.uuid)])
        self.sub_null = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.user)

    def tearDown(self):

        # Cleanup Structs
        self.sub_null.delete()
        self.sub_bad.delete()
        self.sub_good.delete()
        self.tst_fork.delete()
        self.tst_busy.delete()
        self.tst_hang.delete()
        self.tst_stdin.delete()
        self.tst_args.delete()
        self.asn.delete()
        self.sub_file_bad.delete()
        self.sub_file_good.delete()
        self.pgm_hang.delete()
        self.pgm_busy.delete()
        self.pgm_fork.delete()
        self.tst_file_stdin.delete()
        self.tst_file_args.delete()

        # Call Parent
        super(RunTestCaseScript, self).tearDown()

    def test_execute_run_args_good(self):

        # Test Good
        run = self.sub_good.execute_run(self.tst_args, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertEqual(int(run['retcode']), 0)
        self.assertTrue(run['output'])
        self.assertEqual(float(run['score']), 10)
        run.delete()

    def test_execute_run_args_bad(self):

        # Test Bad
        run = self.sub_bad.execute_run(self.tst_args, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertEqual(int(run['retcode']), 0)
        self.assertTrue(run['output'])
        self.assertLess(float(run['score']), 10)
        run.delete()

    def test_execute_run_stdin_good(self):

        # Test Good
        run = self.sub_good.execute_run(self.tst_stdin, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertEqual(int(run['retcode']), 0)
        self.assertTrue(run['output'])
        self.assertEqual(float(run['score']), 10)
        run.delete()

    def test_execute_run_stdin_bad(self):

        # Test Bad
        run = self.sub_bad.execute_run(self.tst_stdin, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertEqual(int(run['retcode']), 0)
        self.assertTrue(run['output'])
        self.assertLess(float(run['score']), 10)
        run.delete()

    def test_execute_run_parallel(self):

        # Start Runs
        runs = []
        for i in range(25):
            run = self.sub_good.execute_run(self.tst_args, workers=self.workers, owner=self.user)
            self.assertTrue(run)
            self.assertNotEqual(run['status'], "complete")
            runs.append(run)

        # Wait for Completion
        for run in runs:
            while not run.is_complete():
                time.sleep(1)

        # Check Output
        for run in runs:
            self.assertEqual(run['status'], "complete")
            self.assertEqual(int(run['retcode']), 0)
            self.assertTrue(run['output'])
            self.assertEqual(float(run['score']), 10)

        # Cleanup
        for run in runs:
            run.delete()

    def test_execute_run_hang(self):

        # Test Hang
        run = self.sub_null.execute_run(self.tst_hang, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertEqual(int(run['retcode']), 124)
        self.assertFalse(run['output'])
        run.delete()

    def test_execute_run_busy(self):

        # Test Busy
        run = self.sub_null.execute_run(self.tst_busy, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertNotEqual(int(run['retcode']), 0)
        self.assertFalse(run['output'])
        run.delete()

    def test_execute_run_fork(self):

        # Test Fork
        run = self.sub_null.execute_run(self.tst_fork, workers=self.workers, owner=self.user)
        self.assertTrue(run)
        self.assertNotEqual(run['status'], "complete")
        while not run.is_complete():
            time.sleep(1)
        self.assertEqual(run['status'], "complete")
        self.assertNotEqual(int(run['retcode']), 0)
        self.assertTrue(run['output'])
        run.delete()


class RunTestCaseIO(test_common_backend.SubMixin,
                    test_common_backend.UUIDHashMixin,
                    StructsTestCase):

    def setUp(self):

        # Call Parent
        super(RunTestCaseIO, self).setUp()

        # Create Hanging Script
        file_bse = open("{:s}/pgm_hang.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="pgm.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.pgm_hang = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Busy Script
        file_bse = open("{:s}/pgm_busy.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="pgm.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.pgm_busy = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Forkbomb Script
        file_bse = open("{:s}/pgm_forkbomb.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="pgm.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'script'
        self.pgm_fork = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Good Sub File
        file_bse = open("{:s}/add_good.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="add.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'submission'
        self.sub_file_good = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Bad Sub File
        file_bse = open("{:s}/add_bad.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="add.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'submission'
        self.sub_file_bad = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Ref Sub File
        file_bse = open("{:s}/add_good.py".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="add.py")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'solution'
        self.sol_file = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Input 1
        file_bse = open("{:s}/add_input1.txt".format(test_common.TEST_INPUT_PATH), 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=file_bse, filename="input1.txt")
        data = copy.copy(test_common.FILE_TESTDICT)
        data['key'] = 'input'
        self.input_file_1 = self.srv.create_file(data, file_obj=file_obj, owner=self.user)
        file_obj.close()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, owner=self.user)

        # Create Tests
        data = copy.copy(test_common.TEST_TESTDICT)
        data['tester'] = "io"
        self.tst = self.asn.create_test(data, owner=self.user)
        self.tst.add_files([str(self.sol_file.uuid)])
        self.tst.add_files([str(self.input_file_1.uuid)])

        # Create Submissions
        self.sub_good = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.user)
        self.sub_good.add_files([str(self.sub_file_good.uuid)])
        self.sub_bad = self.asn.create_submission(test_common.SUBMISSION_TESTDICT, owner=self.user)
        self.sub_bad.add_files([str(self.sub_file_bad.uuid)])

    def tearDown(self):

        # Cleanup Structs
        self.sub_bad.delete()
        self.sub_good.delete()
        self.tst.delete()
        self.asn.delete()
        self.input_file_1.delete()
        self.sol_file.delete()
        self.sub_file_bad.delete()
        self.sub_file_good.delete()

        # Call Parent
        super(RunTestCaseIO, self).tearDown()

    def test_execute_run_args_good(self):
        pass

        # Test Good
        # run = self.sub_good.execute_run(self.tst_args, workers=self.workers, owner=self.user)
        # self.assertTrue(run)
        # self.assertNotEqual(run['status'], "complete")
        # while not run.is_complete():
        #     time.sleep(1)
        # self.assertEqual(run['status'], "complete")
        # self.assertEqual(int(run['retcode']), 0)
        # self.assertTrue(run['output'])
        # self.assertEqual(float(run['score']), 10)
        # run.delete()


# Main
if __name__ == '__main__':
    unittest.main()
