#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest
import werkzeug

import structs
import test_common


class TypesTestCase(test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(TypesTestCase, self).setUp()

        # Setup Server
        self.srv = structs.Server(db=self.db)

        # Setup Admin
        self.admin = self.srv._create_user(test_common.USER_TESTDICT)
        self.admin_uuid = str(self.admin.uuid).lower()
        self.srv.add_admins([self.admin_uuid])

    def tearDown(self):
        super(TypesTestCase, self).tearDown()

    def subHashDirectHelper(self, hash_create, hash_get, hash_list, input_dict,
                            extra_kwargs={}, extra_objs=None, user=None):

        if extra_objs:
            uuids_in = set(extra_objs)
        else:
            uuids_in = set([])

        # List UUIDs (Empty DB)
        uuids_out = hash_list(user=user)
        self.assertEqual(uuids_in, uuids_out)

        # Generate 10 Objects
        objects = []
        for i in range(10):
            obj = hash_create(input_dict, user=user, **extra_kwargs)
            self.assertSubset(input_dict, obj.get_dict())
            objects.append(obj)
            uuids_in.add(str(obj.uuid))

        # List UUIDs
        uuids_out = hash_list(user=user)
        self.assertEqual(uuids_in, uuids_out)

        # Check Objects
        for obj_in in objects:
            obj_out = hash_get(str(obj_in.uuid), user=user)
            self.assertEqual(obj_in, obj_out)
            self.assertSubset(obj_in.get_dict(), obj_out.get_dict())

        # Delete Objects
        for obj_in in objects:
            uuid = str(obj_in.uuid)
            obj_in.delete(user=user)
            self.assertFalse(obj_in.exists())
            uuids_in.remove(uuid)

        # List UUIDs (Empty DB)
        uuids_out = hash_list(user=user)
        self.assertEqual(uuids_in, uuids_out)


    def subSetReferenceHelper(self, set_add, set_rem, set_list, uuids,
                              extra_uuids=None, user=None):

        uuids_in = set(uuids)

        if extra_uuids:
            objects_in = set(extra_uuids)
        else:
            objects_in = set([])

        # List Objects (Empty DB)
        objects_out = set_list(user=user)
        self.assertEqual(objects_in, objects_out)

        # Add Set
        self.assertEqual(set_add(set(uuids_in), user=user), len(uuids_in))
        objects_in.update(set(uuids_in))

        # List Objects
        objects_out = set_list(user=user)
        self.assertEqual(objects_in, objects_out)

        # Remove Some Objects
        for i in range(len(uuids_in)/2):
            k = uuids_in.pop()
            self.assertEqual(set_rem(set([k]), user=user), 1)
            objects_in.remove(k)

        # List Objects
        objects_out = set_list(user=user)
        self.assertEqual(objects_in, objects_out)

        # Remove Remaining Objects
        self.assertEqual(set_rem(uuids_in, user=user), len(uuids_in))
        objects_in.difference_update(set(uuids_in))

        # List Objects (Empty List)
        objects_out = set_list(user=user)
        self.assertEqual(objects_in, objects_out)

    def hashCreateHelper(self, hash_create, input_dict, user=None):

        # Test Empty Dict
        d = {}
        self.assertRaises(KeyError, hash_create, d, user=user)

        # Test Bad Dict
        d = {'badkey': "test"}
        self.assertRaises(KeyError, hash_create, d, user=user)

        # Test Sub Dict
        d = copy.copy(input_dict)
        d.pop(d.keys()[0])
        self.assertRaises(KeyError, hash_create, d, user=user)

        # Test Super Dict
        d = copy.copy(input_dict)
        d['badkey'] = "test"
        self.assertRaises(KeyError, hash_create, d, user=user)

        # Test Good Dict
        obj = hash_create(input_dict, user=user)
        self.assertSubset(input_dict, obj.get_dict())

    def hashGetHelper(self, hash_create, hash_get, input_dict, user=None):

        # Test Invalid UUID
        self.assertRaises(structs.ObjectDNE,
                          hash_get,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf',
                          user=user)

        # Test Valid UUID
        obj1 = hash_create(input_dict, user=user)
        self.assertSubset(input_dict, obj1.get_dict())
        obj1_key = obj1.obj_key
        obj2 = hash_get(obj1_key, user=user)
        self.assertEqual(obj1, obj2)
        self.assertEqual(obj1.get_dict(), obj2.get_dict())

    def hashUpdateHelper(self, hash_create, input_dict, user=None):

        # Create Obj
        obj = hash_create(input_dict, user=user)
        self.assertSubset(input_dict, obj.get_dict())

        # Update Obj
        update_dict = {}
        for k in input_dict:
            update_dict[k] = "{:s}_updated".format(input_dict[k])
        obj.update(update_dict, user=user)
        self.assertSubset(update_dict, obj.get_dict())

    def hashDeleteHelper(self, hash_create, input_dict, user=None):

        # Test Valid UUID
        obj = hash_create(input_dict, user=user)
        obj.delete(user=user)
        self.assertFalse(obj.exists())


class ServerTestCase(TypesTestCase):

    def setUp(self):
        super(ServerTestCase, self).setUp()

    def tearDown(self):
        super(ServerTestCase, self).tearDown()

    def test_users(self):
        self.subHashDirectHelper(self.srv.create_user,
                                 self.srv.get_user,
                                 self.srv.list_users,
                                 test_common.USER_TESTDICT,
                                 extra_objs=[self.admin_uuid],
                                 user=self.admin)

    def test_groups(self):
        self.subHashDirectHelper(self.srv.create_group,
                                 self.srv.get_group,
                                 self.srv.list_groups,
                                 test_common.GROUP_TESTDICT,
                                 extra_objs=[structs.auth._SPECIAL_GROUP_ADMIN],
                                 user=self.admin)

    def test_files(self):
        src_file = open("./Makefile", 'rb')
        file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename="Makefile")
        self.subHashDirectHelper(self.srv.create_file,
                                 self.srv.get_file,
                                 self.srv.list_files,
                                 test_common.FILE_TESTDICT,
                                 extra_kwargs={'file_obj': file_obj},
                                 user=self.admin)

    def test_assignments(self):
        self.subHashDirectHelper(self.srv.create_assignment,
                                 self.srv.get_assignment,
                                 self.srv.list_assignments,
                                 test_common.ASSIGNMENT_TESTDICT,
                                 user=self.admin)

    def test_tests(self):
        asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, user=self.admin)
        self.subHashDirectHelper(asn.create_test,
                                 self.srv.get_test,
                                 asn.list_tests,
                                 test_common.TEST_TESTDICT,
                                 user=self.admin)



class UserTestCase(TypesTestCase):

    def setUp(self):
        super(UserTestCase, self).setUp()

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def test_create_user(self):
        self.hashCreateHelper(self.srv.create_user,
                              test_common.USER_TESTDICT,
                              user=self.admin)

    def test_get_user(self):
        self.hashGetHelper(self.srv.create_user,
                           self.srv.get_user,
                           test_common.USER_TESTDICT,
                           user=self.admin)

    def test_update_user(self):
        self.hashUpdateHelper(self.srv.create_user,
                              test_common.USER_TESTDICT,
                              user=self.admin)

    def test_delete_user(self):
        self.hashDeleteHelper(self.srv.create_user,
                              test_common.USER_TESTDICT,
                              user=self.admin)


class GroupTestCase(TypesTestCase):

    def setUp(self):
        super(GroupTestCase, self).setUp()
        self.users = set([])
        for i in range(10):
            d = copy.copy(test_common.USER_TESTDICT)
            for k in d:
                d[k] = "test_{:s}_{:02d}".format(k, i)
            self.users.add(str(self.srv._create_user(d).uuid))

    def tearDown(self):
        super(GroupTestCase, self).tearDown()

    def test_create_group(self):
        self.hashCreateHelper(self.srv.create_group,
                              test_common.GROUP_TESTDICT,
                              user=self.admin)

    def test_get_group(self):
        self.hashGetHelper(self.srv.create_group,
                           self.srv.get_group,
                           test_common.GROUP_TESTDICT,
                           user=self.admin)

    def test_delete_group(self):
        self.hashDeleteHelper(self.srv.create_group,
                              test_common.GROUP_TESTDICT,
                              user=self.admin)

    def test_update_group(self):
        self.hashUpdateHelper(self.srv.create_group,
                              test_common.GROUP_TESTDICT,
                              user=self.admin)

    def test_members(self):
        grp = self.srv.create_group(test_common.GROUP_TESTDICT, user=self.admin)
        self.subSetReferenceHelper(grp.add_users, grp.rem_users, grp.list_users,
                                   self.users, user=self.admin)


class AssignmentTestCase(TypesTestCase):

    def setUp(self):
        super(AssignmentTestCase, self).setUp()

    def tearDown(self):
        super(AssignmentTestCase, self).tearDown()

    def test_create_assignment(self):
        self.hashCreateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              user=self.admin)

    def test_get_assignment(self):
        self.hashGetHelper(self.srv.create_assignment,
                           self.srv.get_assignment,
                           test_common.ASSIGNMENT_TESTDICT,
                           user=self.admin)

    def test_update_assignment(self):
        self.hashUpdateHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              user=self.admin)

    def test_delete_assignment(self):
        self.hashDeleteHelper(self.srv.create_assignment,
                              test_common.ASSIGNMENT_TESTDICT,
                              user=self.admin)

# class TestTestCase(TypesTestCase):

#     def setUp(self):
#         super(TestTestCase, self).setUp()
#         self.asn = self.srv.create_assignment(test_common.ASSIGNMENT_TESTDICT, user=self.admin)

#     def tearDown(self):
#         super(TestTestCase, self).tearDown()

#     def test_create_test(self):
#         self.hashCreateHelper(self.asn.create_test,
#                               test_common.TEST_TESTDICT,
#                               user=self.admin)

#     def test_get_test(self):
#         self.hashGetHelper(self.asn.create_test,
#                            self.asn.get_test,
#                            test_common.TEST_TESTDICT,
#                            user=self.admin)


# Main
if __name__ == '__main__':
    unittest.main()
