#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest
import werkzeug
import os

import structs
import test_common

class TypesTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(TypesTestCase, self).setUp()

        # Setup Server
        self.srv = structs.Server(db=self.db)

    def tearDown(self):

        # Call parent
        super(TypesTestCase, self).tearDown()

    def subHashDirectHelper(self, hash_create, hash_get, hash_list, input_dict,
                            base_kwargs={}, extra_kwargs={}, extra_objs=None):

        if extra_objs:
            uuids_in = set(extra_objs)
        else:
            uuids_in = set([])

        # List UUIDs (Empty DB)
        uuids_out = hash_list()
        self.assertEqual(uuids_in, uuids_out)

        # Generate 10 Objects
        objects = []
        for i in range(10):
            kwargs = copy.copy(extra_kwargs)
            for kwarg in base_kwargs:
                kwargs[kwarg] = "{:s}_{:02d}".format(base_kwargs[kwarg], i)
            obj = hash_create(input_dict, **kwargs)
            self.assertSubset(input_dict, obj.get_dict())
            objects.append(obj)
            uuids_in.add(str(obj.uuid))

        # List UUIDs
        uuids_out = hash_list()
        self.assertEqual(uuids_in, uuids_out)

        # Check Objects
        for obj_in in objects:
            obj_out = hash_get(str(obj_in.uuid))
            self.assertEqual(obj_in, obj_out)
            self.assertSubset(obj_in.get_dict(), obj_out.get_dict())

        # Delete Objects
        for obj_in in objects:
            uuid = str(obj_in.uuid)
            obj_in.delete()
            self.assertFalse(obj_in.exists())
            uuids_in.remove(uuid)

        # List UUIDs (Empty DB)
        uuids_out = hash_list()
        self.assertEqual(uuids_in, uuids_out)


    def subSetReferenceHelper(self, set_add, set_rem, set_list, uuids,
                              extra_uuids=None):

        uuids_in = set(uuids)

        if extra_uuids:
            objects_in = set(extra_uuids)
        else:
            objects_in = set([])

        # List Objects (Empty DB)
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

        # Add Set
        self.assertEqual(set_add(set(uuids_in)), len(uuids_in))
        objects_in.update(set(uuids_in))

        # List Objects
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

        # Remove Some Objects
        for i in range(len(uuids_in)/2):
            k = uuids_in.pop()
            self.assertEqual(set_rem(set([k])), 1)
            objects_in.remove(k)

        # List Objects
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

        # Remove Remaining Objects
        self.assertEqual(set_rem(uuids_in), len(uuids_in))
        objects_in.difference_update(set(uuids_in))

        # List Objects (Empty List)
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

    def hashCreateHelper(self, hash_create, input_dict, extra_kwargs={}):

        if input_dict:
            # Test Empty Dict
            d = {}
            self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        if input_dict:
            # Test Sub Dict
            d = copy.copy(input_dict)
            d.pop(d.keys()[0])
            self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        # Test Bad Dict
        d = {'badkey': "test"}
        self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        # Test Super Dict
        d = copy.copy(input_dict)
        d['badkey'] = "test"
        self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        # Test Good Dict
        obj = hash_create(input_dict, **extra_kwargs)
        self.assertSubset(input_dict, obj.get_dict())

        # Delete Obj
        obj.delete()
        self.assertFalse(obj.exists())

    def hashGetHelper(self, hash_create, hash_get, input_dict, extra_kwargs={}):

        # Test Invalid UUID
        self.assertRaises(structs.ObjectDNE,
                          hash_get,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf')

        # Test Valid UUID
        obj1 = hash_create(input_dict, **extra_kwargs)
        self.assertSubset(input_dict, obj1.get_dict())
        obj1_key = obj1.obj_key
        obj2 = hash_get(obj1_key)
        self.assertEqual(obj1, obj2)
        self.assertEqual(obj1.get_dict(), obj2.get_dict())

        # Delete Obj
        obj1.delete()
        self.assertFalse(obj1.exists())

    def hashUpdateHelper(self, hash_create, input_dict, extra_kwargs={}):

        # Create Obj
        obj = hash_create(input_dict, **extra_kwargs)
        self.assertSubset(input_dict, obj.get_dict())

        # Update Obj
        update_dict = {}
        for k in input_dict:
            update_dict[k] = "{:s}_updated".format(input_dict[k])
        obj.update(update_dict)
        self.assertSubset(update_dict, obj.get_dict())

        # Delete Obj
        obj.delete()
        self.assertFalse(obj.exists())

    def hashDeleteHelper(self, hash_create, input_dict, extra_kwargs={}):

        # Test Valid UUID
        obj = hash_create(input_dict, **extra_kwargs)
        obj.delete()
        self.assertFalse(obj.exists())


class ServerTestCase(TypesTestCase):

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
                                 extra_kwargs={'file_obj': file_obj})
        file_obj.close()

    def test_assignments(self):
        self.subHashDirectHelper(self.srv.create_assignment,
                                 self.srv.get_assignment,
                                 self.srv.list_assignments,
                                 test_common.ASSIGNMENT_TESTDICT)

    def test_asn_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 asn.list_tests,
                                 test_common.TEST_TESTDICT)
        asn.delete()

    def test_srv_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 self.srv.list_tests,
                                 test_common.TEST_TESTDICT)
        asn.delete()

    def test_asn_submissions(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)
        self.subHashDirectHelper(asn.create_submission,
                                 self.srv.get_submission,
                                 asn.list_submissions,
                                 test_common.SUBMISSION_TESTDICT)
        asn.delete()

    def test_srv_submissions(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)
        self.subHashDirectHelper(asn.create_submission,
                                 self.srv.get_submission,
                                 self.srv.list_submissions,
                                 test_common.SUBMISSION_TESTDICT)
        asn.delete()


class FileTestCase(TypesTestCase):

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
                              extra_kwargs={'file_obj': self.file_obj})

    def test_get_file(self):
        self.hashGetHelper(self.srv.create_file,
                           self.srv.get_file,
                           test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj})

    def test_update_file(self):
        self.hashUpdateHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj})

    def test_delete_file(self):
        self.hashDeleteHelper(self.srv.create_file,
                              test_common.FILE_TESTDICT,
                              extra_kwargs={'file_obj': self.file_obj})


class AssignmentTestCase(TypesTestCase):

    def setUp(self):
        super(AssignmentTestCase, self).setUp()

    def tearDown(self):
        super(AssignmentTestCase, self).tearDown()

    def test_create_assignment(self):
        self.hashCreateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT)

    def test_get_assignment(self):
        self.hashGetHelper(self.srv.create_assignment,
                           self.srv.get_assignment,
                           test_common.ASSIGNMENT_TESTDICT)

    def test_update_assignment(self):
        self.hashUpdateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT)

    def test_delete_assignment(self):
        self.hashDeleteHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT)


class TestTestCase(TypesTestCase):

    def setUp(self):

        # Call Parent
        super(TestTestCase, self).setUp()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)

        # Create Files
        src_file = open("./Makefile", 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, file_obj=file_obj).uuid))
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
                              test_common.TEST_TESTDICT)

    def test_get_test(self):
        self.hashGetHelper(self.asn.create_test,
                           self.srv.get_test,
                           test_common.TEST_TESTDICT)

    def test_update_test(self):
        self.hashUpdateHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT)

    def test_delete_test(self):
        self.hashDeleteHelper(self.asn.create_test,
                              test_common.TEST_TESTDICT)

    def test_files(self):
        tst = self.asn.create_test(test_common.TEST_TESTDICT)
        self.subSetReferenceHelper(tst.add_files, tst.rem_files, tst.list_files, self.files)
        tst.delete()


class SubmissionTestCase(TypesTestCase):

    def setUp(self):

        # Call Parent
        super(SubmissionTestCase, self).setUp()

        # Create Assignment
        self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT)

        # Create Files
        src_file = open("./Makefile", 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")
        self.files = set([])
        for i in range(10):
            data = copy.copy(test_common.FILE_TESTDICT)
            for k in data:
                data[k] = "test_{:s}_{:02d}".format(k, i)
            self.files.add(str(self.srv.create_file(data, file_obj=file_obj).uuid))
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
                              test_common.SUBMISSION_TESTDICT)

    def test_get_submission(self):
        self.hashGetHelper(self.asn.create_submission,
                           self.srv.get_submission,
                           test_common.SUBMISSION_TESTDICT)

    def test_update_submission(self):
        self.hashUpdateHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT)

    def test_delete_submission(self):
        self.hashDeleteHelper(self.asn.create_submission,
                              test_common.SUBMISSION_TESTDICT)

    def test_files(self):
        sub = self.asn.create_submission(test_common.SUBMISSION_TESTDICT)
        self.subSetReferenceHelper(sub.add_files, sub.rem_files, sub.list_files, self.files)
        sub.delete()


# Main
if __name__ == '__main__':
    unittest.main()
