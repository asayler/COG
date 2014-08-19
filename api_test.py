#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import base64
import copy
import json
import unittest
import uuid
import os

import cogs.test_common

import api


class CogsApiTestCase(cogs.test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(CogsApiTestCase, self).setUp()

        # Set App to Testing Mode
        api.app.testing = True

        # Create Test Client
        self.app = api.app.test_client()

        # Setup Admin
        self.admin = api.auth.create_user(cogs.test_common.USER_TESTDICT,
                                          username=cogs.test_common.ADMIN_USERNAME,
                                          password=cogs.test_common.ADMIN_PASSWORD,
                                          authmod=cogs.test_common.ADMIN_AUTHMOD)
        self.admin_uuid = str(self.admin.uuid).lower()
        api.auth.add_admins([self.admin_uuid])

    def tearDown(self):

        # Remove User
        self.admin.delete()

        # Call Parent
        super(CogsApiTestCase, self).tearDown()

    ## Auth Helpers ##

    def open_auth(self, method, url, username=None, password=None, **kwargs):

        headers = kwargs.pop('headers', {})

        if username:
            if not password:
                password = ""
            auth_str = "{:s}:{:s}".format(username, password)
            b64_auth_str = base64.b64encode(auth_str)
            key = "Authorization"
            val = "Basic {:s}".format(b64_auth_str)
            headers[key] = val

        return self.app.open(url, method=method, headers=headers, **kwargs)

    def open_user(self, method, url, user=None, **kwargs):

        if user:
            username = user['token']
        else:
            username = None

        return self.open_auth(method, url, username=username, **kwargs)

class CogsApiObjectBase(object):

    ## Object Helpers ##

    def create_objects(self, url, key, data, user=None):
        data = json.dumps(data)
        res = self.open_user('POST', url, user=user, data=data)
        self.assertEqual(res.status_code, 200)
        res_obj = json.loads(res.data)
        self.assertTrue(res_obj)
        res_keys = res_obj.keys()
        self.assertEqual(len(res_keys), 1)
        self.assertEqual(res_keys[0], key)
        res_lst = res_obj[key]
        self.assertEqual(len(res_lst), 1)
        res_uuid = res_lst[0]
        self.assertTrue(res_uuid)
        return res_uuid

    def lst_objects(self, url, key, user=None):
        res = self.open_user('GET', url, user=user)
        self.assertEqual(res.status_code, 200)
        res_obj = json.loads(res.data)
        self.assertTrue(res_obj)
        res_keys = res_obj.keys()
        self.assertEqual(len(res_keys), 1)
        self.assertEqual(res_keys[0], key)
        res_lst = res_obj[key]
        return set(res_lst)

    def get_object(self, url, obj_uuid, user=None):
        res = self.open_user('GET', '{:s}{:s}/'.format(url, obj_uuid), user=user)
        if (res.status_code == 200):
            self.assertEqual(res.status_code, 200)
            res_obj = json.loads(res.data)
            self.assertTrue(res_obj)
            res_keys = res_obj.keys()
            self.assertEqual(len(res_keys), 1)
            self.assertEqual(res_keys[0], obj_uuid)
            res_hash = res_obj[obj_uuid]
            self.assertTrue(res_hash)
            return res_hash
        elif (res.status_code == 404):
            return None
        else:
            self.fail("Bad HTTP status code {:d}".format(res.status_code))

    def set_object(self, url, obj_uuid, data, user=None):
        data = json.dumps(data)
        res = self.open_user('PUT', '{:s}{:s}/'.format(url, obj_uuid), user=user, data=data)
        if (res.status_code == 200):
            self.assertEqual(res.status_code, 200)
            res_obj = json.loads(res.data)
            self.assertTrue(res_obj)
            res_keys = res_obj.keys()
            self.assertEqual(len(res_keys), 1)
            self.assertEqual(res_keys[0], obj_uuid)
            res_hash = res_obj[obj_uuid]
            self.assertTrue(res_hash)
            return res_hash
        elif (res.status_code == 404):
            return None
        else:
            self.fail("Bad HTTP status code {:d}".format(res.status_code))

    def delete_object(self, url, obj_uuid, user=None):
        res = self.open_user('DELETE', '{:s}{:s}/'.format(url, obj_uuid), user=user)
        if (res.status_code == 200):
            self.assertEqual(res.status_code, 200)
            res_obj = json.loads(res.data)
            self.assertTrue(res_obj)
            res_keys = res_obj.keys()
            self.assertEqual(len(res_keys), 1)
            self.assertEqual(res_keys[0], obj_uuid)
            res_hash = res_obj[obj_uuid]
            self.assertTrue(res_hash)
            return res_hash
        elif (res.status_code == 404):
            return None
        else:
            self.fail("Bad HTTP status code {:d}".format(res.status_code))

    ## Object Tests ##

    def test_create_object(self):

        obj_uuid = self.create_objects(self.url, self.key, self.data, user=self.user)
        self.assertTrue(obj_uuid)

    def test_list_objects(self):

        objects_in = set([])

        # Get Object List (Empty)
        objects_out = self.lst_objects(self.url, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

        # Create Objects
        for i in range(10):
            obj_uuid = self.create_objects(self.url, self.key, self.data, user=self.user)
            objects_in.add(obj_uuid)

        # Get Object List
        objects_out = self.lst_objects(self.url, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

        # Delete Some Objects
        for i in range(5):
            obj_uuid = objects_in.pop()
            self.delete_object(self.url, obj_uuid, user=self.user)

        # Get Objects
        objects_out = self.lst_objects(self.url, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

        # Delete Remaining Objects
        for obj_uuid in list(objects_in):
            objects_in.remove(obj_uuid)
            self.delete_object(self.url, obj_uuid, user=self.user)

        # Get Objects
        objects_out = self.lst_objects(self.url, self.key, user=self.user)
        self.assertEqual(objects_in, objects_out)

    def test_get_object(self):

        # Create Object
        obj_uuid = self.create_objects(self.url, self.key, self.data, user=self.admin)

        # Get Object
        obj = self.get_object(self.url, obj_uuid, user=self.admin)
        self.assertSubset(self.data, obj)

    def test_set_object(self):

        # Create Object
        obj_uuid = self.create_objects(self.url, self.key, self.data, user=self.admin)

        # Update Object
        data = copy.copy(self.data)
        for key in data:
            data[key] = data[key] + "_updated"
        self.assertNotEqual(self.data, data)
        obj = self.set_object(self.url, obj_uuid, data, user=self.admin)
        self.assertSubset(data, obj)

        # Get Object
        obj = self.get_object(self.url, obj_uuid, user=self.admin)
        self.assertSubset(data, obj)

    def test_delete_object(self):

        # Create Object
        obj_uuid = self.create_objects(self.url, self.key, self.data, user=self.admin)

        # Get Object
        obj = self.get_object(self.url, obj_uuid, user=self.admin)
        self.assertSubset(self.data, obj)

        # Delete Object
        self.delete_object(self.url, obj_uuid, user=self.user)

        # Get Object
        obj = self.get_object(self.url, obj_uuid, user=self.admin)
        self.assertIsNone(obj)


## Root Tests ##
class CogsApiRootTestCase(CogsApiTestCase):

    def setUp(self):
        super(CogsApiRootTestCase, self).setUp()

    def tearDown(self):
        super(CogsApiRootTestCase, self).tearDown()

    def test_root_get(self):
        res = self.open_user('GET', '/', user=self.admin)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, api._MSG_ROOT)


## Assignment Tests ##
class CogsApiAssignmentTestCase(CogsApiObjectBase, CogsApiTestCase):

    def setUp(self):
        super(CogsApiAssignmentTestCase, self).setUp()
        self.user = self.admin
        self.url = '/assignments/'
        self.key = 'assignments'
        self.data = copy.copy(cogs.test_common.ASSIGNMENT_TESTDICT)

    def tearDown(self):
        super(CogsApiAssignmentTestCase, self).tearDown()



# ## Assignment Test Tests
# class CogsApiTestTestCase(CogsApiTestHelpers):

#     def setUp(self):

#         # Call Parent setUp()
#         super(CogsApiTestTestCase, self).setUp()

#         # Create Assignment
#         self.asn_uuid = self.create_assignment()

#     def tearDown(self):

#         # Call Parent tearDown()
#         super(CogsApiTestTestCase, self).tearDown()

#     def test_create_test(self):

#         # Create Test
#         tst_uuid = self.create_test()
#         self.assertTrue(tst_uuid)

#     def test_get_test(self):

#         # Create Test
#         tst_uuid = self.create_test(cogs.test_common.TEST_TESTDICT)

#         # Get Test
#         tst = self.get_test(tst_uuid)
#         self.assertSubset(cogs.test_common.TEST_TESTDICT, tst[str(tst_uuid)])

#     def test_set_test(self):

#         # Create Test
#         tst_uuid = self.create_test(cogs.test_common.TEST_TESTDICT)

#         # Update Test
#         d = copy.deepcopy(cogs.test_common.TEST_TESTDICT)
#         for k in d:
#             d[k] = d[k] + "_update"
#         self.assertNotEqual(cogs.test_common.TEST_TESTDICT, d)
#         tst = self.set_test(tst_uuid, d)
#         self.assertSubset(d, tst[str(tst_uuid)])

#         # Get Test
#         tst = self.get_test(tst_uuid)
#         self.assertSubset(d, tst[str(tst_uuid)])

#     def test_delete_test(self):

#         # Create Test
#         tst_uuid = self.create_test(cogs.test_common.TEST_TESTDICT)

#         # Get Test
#         res = self.app.get('/assignments/{:s}/tests/{:s}/'.format(self.asn_uuid, tst_uuid))
#         self.assertEqual(res.status_code, 200)

#         # Delete Test
#         self.delete_test(tst_uuid)

#         # Get Test
#         res = self.app.get('/assignments/{:s}/tests/{:s}/'.format(self.asn_uuid, tst_uuid))
#         self.assertEqual(res.status_code, 404)

#     def test_list_tests(self):

#         tests_in = set([])

#         # Get Tests (Empty)
#         tests_out = self.lst_tests()
#         self.assertEqual(tests_in, tests_out)

#         # Create Tests
#         for i in range(10):
#             d = copy.deepcopy(cogs.test_common.TEST_TESTDICT)
#             for k in d:
#                 d[k] = d[k] + "_{:02d}".format(i)
#             tst_uuid = self.create_test(d)
#             tests_in.add(str(tst_uuid))

#         # Get Tests
#         tests_out = self.lst_tests()
#         self.assertEqual(tests_in, tests_out)

#         # Delete Tests
#         for i in range(5):
#             rmv_uuid = tests_in.pop()
#             self.delete_test(rmv_uuid)

#         # Get Tests
#         tests_out = self.lst_tests()
#         self.assertEqual(tests_in, tests_out)

### Main
if __name__ == '__main__':
    unittest.main()
