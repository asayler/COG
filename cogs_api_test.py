#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import json
import unittest
import uuid

import redis

import cogs_api

_REDIS_TESTDB_OFFSET = 1

_ASSIGNMENTS_KEY = "assignments"
_ASSIGNMENTTESTS_KEY = "tests"

_ASSIGNMENT_TESTDICT      = {'name': "Test_Assignment",
                             'contact': "Andy Sayler"}
_ASSIGNMENTTEST_TESTDICT  = {'name': "Test_Assignment",
                             'contact': "Andy Sayler",
                             'path': "/tmp/test.py",
                             'maxscore': "10"}

class CogsApiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        cogs_api.datatypes._REDIS_DB += _REDIS_TESTDB_OFFSET
        self.db = redis.StrictRedis(host=cogs_api.datatypes._REDIS_HOST,
                                    port=cogs_api.datatypes._REDIS_PORT,
                                    db=cogs_api.datatypes._REDIS_DB)
        if (self.db.dbsize() != 0):
            raise Exception("Test Database Not Empty: {}".format(self.db.dbsize()))
        self.app = cogs_api.app.test_client()

    def tearDown(self):
        self.db.flushdb()
        cogs_api.datatypes._REDIS_DB -= _REDIS_TESTDB_OFFSET


## Root Tests
class CogsApiRootTestCase(CogsApiTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        super(CogsApiRootTestCase, self).setUp()

    def tearDown(self):
        super(CogsApiRootTestCase, self).tearDown()

    def test_root_get(self):
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, cogs_api._MSG_ROOT)


## Assignment Tests
class CogsApiAssignmentsTestCase(CogsApiTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        super(CogsApiAssignmentsTestCase, self).setUp()

    def tearDown(self):
        super(CogsApiAssignmentsTestCase, self).tearDown()

    def test_create_assignment(self):

        # Create Assignment
        ds = json.dumps(_ASSIGNMENT_TESTDICT)
        res = self.app.post('/assignments/', data=ds)
        self.assertEqual(res.status_code, 200)

        # Check Assignment
        asn = json.loads(res.data)
        asn_uuid = uuid.UUID(asn.keys()[0])
        asn_d = asn[str(asn_uuid)]
        self.assertEqual(_ASSIGNMENT_TESTDICT, asn_d)

    def test_get_assignment(self):

        # Create Assignment
        ds = json.dumps(_ASSIGNMENT_TESTDICT)
        res = self.app.post('/assignments/', data=ds)
        self.assertEqual(res.status_code, 200)
        asn_in = json.loads(res.data)
        asn_in_uuid = uuid.UUID(asn_in.keys()[0])

        # Get Assignment
        res = self.app.get('/assignments/{:s}/'.format(asn_in_uuid))
        self.assertEqual(res.status_code, 200)
        asn_out = json.loads(res.data)
        asn_out_uuid = uuid.UUID(asn_out.keys()[0])
        self.assertEqual(asn_in_uuid, asn_out_uuid)
        self.assertEqual(asn_in[str(asn_in_uuid)], asn_out[str(asn_out_uuid)])

    def test_set_assignment(self):

        # Create Assignment
        d_a = copy.deepcopy(_ASSIGNMENT_TESTDICT)
        ds_a = json.dumps(d_a)
        res_a = self.app.post('/assignments/', data=ds_a)
        self.assertEqual(res_a.status_code, 200)
        a_dict = json.loads(res_a.data)
        a_uuid = uuid.UUID(a_dict.keys()[0])

        # Update Assignment
        d_b = copy.deepcopy(_ASSIGNMENT_TESTDICT)
        for k in d_b:
            d_b[k] = d_b[k] + "_update"
        self.assertNotEqual(d_a, d_b)
        ds_b = json.dumps(d_b)
        res_b = self.app.put('/assignments/{:s}/'.format(a_uuid), data=ds_b)
        self.assertEqual(res_b.status_code, 200)
        b_dict = json.loads(res_b.data)
        b_uuid = uuid.UUID(b_dict.keys()[0])
        self.assertEqual(a_uuid, b_uuid)
        self.assertEqual(d_b, b_dict[str(b_uuid)])

        # Get Assignment
        res_c = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_c.status_code, 200)
        c_dict = json.loads(res_c.data)
        c_uuid = uuid.UUID(c_dict.keys()[0])
        self.assertEqual(b_uuid, c_uuid)
        self.assertEqual(b_dict[str(b_uuid)], c_dict[str(c_uuid)])

    def test_delete_assignment(self):

        # Create Assignment
        d_a = copy.deepcopy(_ASSIGNMENT_TESTDICT)
        ds_a = json.dumps(d_a)
        res_a = self.app.post('/assignments/', data=ds_a)
        self.assertEqual(res_a.status_code, 200)
        a_dict = json.loads(res_a.data)
        a_uuid = uuid.UUID(a_dict.keys()[0])
        self.assertEqual(d_a, a_dict[str(a_uuid)])

        # Get Assignment
        res_b = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_b.status_code, 200)
        b_dict = json.loads(res_b.data)
        b_uuid = uuid.UUID(b_dict.keys()[0])
        self.assertEqual(a_uuid, b_uuid)
        self.assertEqual(a_dict[str(a_uuid)], b_dict[str(b_uuid)])

        # Delete Assignment
        res_c = self.app.delete('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_c.status_code, 200)

        # Get Assignment
        res_b = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_b.status_code, 404)

    def test_list_assignments(self):

        assignments_in = set([])

        # Get Assignments (Empty)
        res_a = self.app.get('/assignments/')
        self.assertEqual(res_a.status_code, 200)
        a_dict = json.loads(res_a.data)
        assignments_out = set(a_dict[_ASSIGNMENTS_KEY])
        self.assertEqual(assignments_in, assignments_out)

        # Create Assignments
        for i in range(10):
            d = {'name': "Test_Assignment_List_{:02d}".format(i),
                   'contact': "Andy Sayler"}
            ds = json.dumps(d)
            res = self.app.post('/assignments/', data=ds)
            self.assertEqual(res.status_code, 200)
            r_dict = json.loads(res.data)
            r_uuid = uuid.UUID(r_dict.keys()[0])
            self.assertEqual(d, r_dict[str(r_uuid)])
            assignments_in.add(str(r_uuid))

        # Get Assignments
        res_b = self.app.get('/assignments/')
        self.assertEqual(res_b.status_code, 200)
        b_dict = json.loads(res_b.data)
        assignments_out = set(b_dict[_ASSIGNMENTS_KEY])
        self.assertEqual(assignments_in, assignments_out)

        # Delete Assignments
        for i in range(5):
            r_uuid = assignments_in.pop()
            res_c = self.app.delete('/assignments/{:s}/'.format(r_uuid))
            self.assertEqual(res_c.status_code, 200)

        # Get Assignments
        res_d = self.app.get('/assignments/')
        self.assertEqual(res_d.status_code, 200)
        d_dict = json.loads(res_d.data)
        assignments_out = set(d_dict[_ASSIGNMENTS_KEY])
        self.assertEqual(assignments_in, assignments_out)

## Assignment Test Tests
class CogsApiAssignmentTestsTestCase(CogsApiTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):

        # Call Parent setUp()
        super(CogsApiAssignmentTestsTestCase, self).setUp()

        # Create Assignment
        ds = json.dumps(_ASSIGNMENT_TESTDICT)
        res = self.app.post('/assignments/', data=ds)
        self.assertEqual(res.status_code, 200)
        self.asn = json.loads(res.data)
        self.asn_uuid = uuid.UUID(self.asn.keys()[0])

    def tearDown(self):

        # Delete Assignment
        res = self.app.delete('/assignments/{:s}/'.format(self.asn_uuid))
        self.assertEqual(res.status_code, 200)

        # Call Parent tearDown()
        super(CogsApiAssignmentTestsTestCase, self).tearDown()

    def test_create_assignment_test(self):

        # Create Assignment Test
        ds = json.dumps(_ASSIGNMENTTEST_TESTDICT)
        res = self.app.post('/assignments/{:s}/tests/'.format(self.asn_uuid), data=ds)
        self.assertEqual(res.status_code, 200)

        # Check test
        tst = json.loads(res.data)
        tst_uuid = uuid.UUID(tst.keys()[0])
        tst_d = tst[str(tst_uuid)]
        self.assertEqual(_ASSIGNMENTTEST_TESTDICT, tst_d)

    def test_get_assignment_test(self):

        # Create Assignment Test
        ds = json.dumps(_ASSIGNMENTTEST_TESTDICT)
        res = self.app.post('/assignments/{:s}/tests/'.format(self.asn_uuid), data=ds)
        self.assertEqual(res.status_code, 200)
        tst_in = json.loads(res.data)
        tst_in_uuid = uuid.UUID(tst_in.keys()[0])

        # Get Assignment
        res = self.app.get('/assignments/{:s}/tests/{:s}/'.format(self.asn_uuid, tst_in_uuid))
        self.assertEqual(res.status_code, 200)
        tst_out = json.loads(res.data)
        tst_out_uuid = uuid.UUID(tst_out.keys()[0])
        self.assertEqual(tst_in_uuid, tst_out_uuid)
        self.assertEqual(tst_in[str(tst_in_uuid)], tst_out[str(tst_out_uuid)])


### Main
if __name__ == '__main__':
    unittest.main()
