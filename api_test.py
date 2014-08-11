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

import api
import cogs.test_common


class CogsApiTestCase(cogs.test_common.CogsTestCase):

    def setUp(self):

        # Call Parent
        super(CogsApiTestCase, self).setUp()

        # Set API active DB to Test DB
        api.db = self.db
        api.srv = api.cogs.structs.Server(api.db)
        assert(api.db == self.db)
        assert(api.srv.db == self.db)

        # Create Test Client
        self.app = api.app.test_client()

        # Setup Admin
        self.admin = api.srv._create_user(cogs.test_common.USER_TESTDICT,
                                          username=cogs.test_common.COGS_ADMIN_USERNAME,
                                          password=cogs.test_common.COGS_ADMIN_PASSWORD,
                                          authmod=cogs.test_common.COGS_ADMIN_AUTH_MOD)
        self.admin_uuid = str(self.admin.uuid).lower()
        api.srv.add_admins([self.admin_uuid])

    def tearDown(self):
        super(CogsApiTestCase, self).tearDown()

    def open_auth(self, method, url, username, password=None):
        if not password:
            password = ""
        auth_str = "{:s}:{:s}".format(username, password)
        b64_auth_str = base64.b64encode(auth_str)
        key = "Authorization"
        val = "Basic {:s}".format(b64_auth_str)
        headers = {key: val}
        return self.app.open(url, method=method, headers=headers)


class CogsApiAssignmentHelpers(CogsApiTestCase):

    def setUp(self):
        super(CogsApiAssignmentHelpers, self).setUp()

    def tearDown(self):
        super(CogsApiAssignmentHelpers, self).tearDown()

    def lst_assignments(self):
        # List Assignments
        res = self.app.get('/assignments/')
        self.assertEqual(res.status_code, 200)
        asn_lst = json.loads(res.data)[api._ASSIGNMENTS_KEY]
        return set(asn_lst)

    def create_assignment(self, d=cogs.test_common.ASSIGNMENT_TESTDICT):
        # Create Assignment
        ds = json.dumps(d)
        res = self.app.post('/assignments/', data=ds)
        self.assertEqual(res.status_code, 200)
        asn_lst = json.loads(res.data)[api._ASSIGNMENTS_KEY]
        self.assertEqual(len(asn_lst), 1)
        asn_uuid = uuid.UUID(asn_lst[0])
        self.assertTrue(asn_uuid)
        return asn_uuid

    def get_assignment(self, asn_uuid):
        # Get Assignment
        res = self.app.get('/assignments/{:s}/'.format(asn_uuid))
        self.assertEqual(res.status_code, 200)
        asn_out = json.loads(res.data)
        asn_out_uuid = uuid.UUID(asn_out.keys()[0])
        self.assertEqual(asn_uuid, asn_out_uuid)
        return asn_out

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


## Root Tests
class CogsApiRootTestCase(CogsApiTestCase):

    def setUp(self):
        super(CogsApiRootTestCase, self).setUp()

    def tearDown(self):
        super(CogsApiRootTestCase, self).tearDown()

    def test_root_get(self):
        res = self.open_auth('GET', '/', self.admin['token'], None)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, api._MSG_ROOT)


## Assignment Tests
# class CogsApiAssignmentTestCase(CogsApiAssignmentHelpers):

#     def setUp(self):
#         super(CogsApiAssignmentTestCase, self).setUp()

#     def tearDown(self):
#         super(CogsApiAssignmentTestCase, self).tearDown()

#     def test_create_assignment(self):

#         # Create Assignment
#         asn_uuid = self.create_assignment()
#         self.assertTrue(asn_uuid)

#     def test_get_assignment(self):

#         # Create Assignment
#         asn_uuid = self.create_assignment(cogs.test_common.ASSIGNMENT_TESTDICT)

#         # Get Assignment
#         asn = self.get_assignment(asn_uuid)
#         self.assertSubset(cogs.test_common.ASSIGNMENT_TESTDICT, asn[str(asn_uuid)])

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

#     def test_list_assignments(self):

#         assignments_in = set([])

#         # Get Assignments (Empty)
#         assignments_out = self.lst_assignments()
#         self.assertEqual(assignments_in, assignments_out)

#         # Create Assignments
#         for i in range(10):
#             d = copy.deepcopy(cogs.test_common.ASSIGNMENT_TESTDICT)
#             for k in d:
#                 d[k] = d[k] + "_{:02d}".format(i)
#             asn_uuid = self.create_assignment(d)
#             assignments_in.add(str(asn_uuid))

#         # Get Assignments
#         assignments_out = self.lst_assignments()
#         self.assertEqual(assignments_in, assignments_out)

#         # Delete Assignments
#         for i in range(5):
#             rmv_uuid = assignments_in.pop()
#             self.delete_assignment(rmv_uuid)

#         # Get Assignments
#         assignments_out = self.lst_assignments()
#         self.assertEqual(assignments_in, assignments_out)


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
