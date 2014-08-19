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
        res = self.open_auth('GET', url, user['token'])
        self.assertEqual(res.status_code, 200)
        res_obj = json.loads(res.data)
        self.assertTrue(res_obj)
        res_keys = res_obj.keys()
        self.assertEqual(len(res_keys), 1)
        self.assertEqual(res_keys[0], key)
        res_lst = res_obj[key]
        return set(res_lst)


class CogsApiAssignmentHelpers(CogsApiTestCase):

    def setUp(self):
        super(CogsApiAssignmentHelpers, self).setUp()

    def tearDown(self):
        super(CogsApiAssignmentHelpers, self).tearDown()

    def get_assignment(self, asn_uuid, user=None):
        # Get Assignment
        res = self.open_user('GET', '/assignments/{:s}'.format(asn_uuid), user=user)
        self.assertEqual(res.status_code, 200)
        asn_out = json.loads(res.data)
        asn_out_uuid = uuid.UUID(asn_out.keys()[0])
        self.assertEqual(asn_uuid, asn_out_uuid)
        return asn_out[asn_uuid]

    def set_assignment(self, asn_uuid, d=cogs.test_common.ASSIGNMENT_TESTDICT):
        # Set Assignment
        ds = json.dumps(d)
        res = self.app.put('/assignments/{:s}/'.format(asn_uuid), data=ds)
        self.assertEqual(res.status_code, 200)
        asn_out = json.loads(res.data)
        asn_out_uuid = uuid.UUID(asn_out.keys()[0])
        self.assertEqual(asn_uuid, asn_out_uuid)
        return asn_out

    def delete_assignment(self, asn_uuid):
        res = self.app.delete('/assignments/{:s}/'.format(asn_uuid))
        self.assertEqual(res.status_code, 200)


class CogsApiTestHelpers(CogsApiAssignmentHelpers):

    def setUp(self):
        super(CogsApiTestHelpers, self).setUp()

    def tearDown(self):
        super(CogsApiTestHelpers, self).tearDown()

    def lst_tests(self):
        # List Tests
        res = self.app.get('/assignments/{:s}/tests/'.format(self.asn_uuid))
        self.assertEqual(res.status_code, 200)
        tst_lst = json.loads(res.data)[api._TESTS_KEY]
        return set(tst_lst)

    def create_test(self, d=cogs.test_common.TEST_TESTDICT):
        # Create Test
        ds = json.dumps(d)
        res = self.app.post('/assignments/{:s}/tests/'.format(self.asn_uuid), data=ds)
        self.assertEqual(res.status_code, 200)
        tst_lst = json.loads(res.data)[api._TESTS_KEY]
        self.assertEqual(len(tst_lst), 1)
        tst_uuid = uuid.UUID(tst_lst[0])
        self.assertTrue(tst_uuid)
        return tst_uuid

    def get_test(self, tst_uuid):
        # Get Test
        res = self.app.get('/assignments/{:s}/tests/{:s}/'.format(self.asn_uuid, tst_uuid))
        self.assertEqual(res.status_code, 200)
        tst_out = json.loads(res.data)
        tst_out_uuid = uuid.UUID(tst_out.keys()[0])
        self.assertEqual(tst_uuid, tst_out_uuid)
        return tst_out

    def set_test(self, tst_uuid, d=cogs.test_common.TEST_TESTDICT):
        # Set Test
        ds = json.dumps(d)
        res = self.app.put('/assignments/{:s}/tests/{:s}/'.format(self.asn_uuid, tst_uuid), data=ds)
        self.assertEqual(res.status_code, 200)
        tst_out = json.loads(res.data)
        tst_out_uuid = uuid.UUID(tst_out.keys()[0])
        self.assertEqual(tst_uuid, tst_out_uuid)
        return tst_out

    def delete_test(self, tst_uuid):
        res = self.app.delete('/assignments/{:s}/tests/{:s}/'.format(self.asn_uuid, tst_uuid))
        self.assertEqual(res.status_code, 200)


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
class CogsApiAssignmentTestCase(CogsApiAssignmentHelpers):

    def setUp(self):
        super(CogsApiAssignmentTestCase, self).setUp()
        self.user = self.admin
        self.url = '/assignments/'
        self.key = 'assignments'
        self.data = copy.copy(cogs.test_common.ASSIGNMENT_TESTDICT)

    def tearDown(self):
        super(CogsApiAssignmentTestCase, self).tearDown()

    def test_create_assignment(self):
        asn_uuid = self.create_objects(self.url, self.key, self.data, user=self.admin)
        self.assertTrue(asn_uuid)

    def test_list_assignments(self):

        assignments_in = set([])

        # Get Assignment List (Empty)
        assignments_out = self.lst_objects(self.url, self.key, user=self.user)
        self.assertEqual(assignments_in, assignments_out)

        # Create Assignments
        for i in range(10):
            asn_uuid = self.create_objects(self.url, self.key, self.data, user=self.user)
            assignments_in.add(asn_uuid)

        # Get Assignment List
        assignments_out = self.lst_objects(self.url, self.key, user=self.user)
        self.assertEqual(assignments_in, assignments_out)

        # # Delete Assignments
        # for i in range(5):
        #     rmv_uuid = assignments_in.pop()
        #     self.delete_assignment(rmv_uuid)

        # # Get Assignments
        # assignments_out = self.lst_assignments()
        # self.assertEqual(assignments_in, assignments_out)


    # def test_get_assignment(self):

    #     # Create Assignment
    #     asn_uuid = self.create_assignment(data=cogs.test_common.ASSIGNMENT_TESTDICT, user=self.admin)

    #     # Get Assignment
    #     asn = self.get_assignment(asn_uuid, user=self.admin)
    #     self.assertSubset(cogs.test_common.ASSIGNMENT_TESTDICT, asn)

#     def test_set_assignment(self):

#         # Create Assignment
#         asn_uuid = self.create_assignment(cogs.test_common.ASSIGNMENT_TESTDICT)

#         # Update Assignment
#         d = copy.deepcopy(cogs.test_common.ASSIGNMENT_TESTDICT)
#         for k in d:
#             d[k] = d[k] + "_update"
#         self.assertNotEqual(cogs.test_common.ASSIGNMENT_TESTDICT, d)
#         asn = self.set_assignment(asn_uuid, d)
#         self.assertSubset(d, asn[str(asn_uuid)])

#         # Get Assignment
#         asn = self.get_assignment(asn_uuid)
#         self.assertSubset(d, asn[str(asn_uuid)])

#     def test_delete_assignment(self):

#         # Create Assignment
#         asn_uuid = self.create_assignment(cogs.test_common.ASSIGNMENT_TESTDICT)

#         # Get Assignment
#         res = self.app.get('/assignments/{:s}/'.format(asn_uuid))
#         self.assertEqual(res.status_code, 200)

#         # Delete Assignment
#         self.delete_assignment(asn_uuid)

#         # Get Assignment
#         res = self.app.get('/assignments/{:s}/'.format(asn_uuid))
#         self.assertEqual(res.status_code, 404)



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
