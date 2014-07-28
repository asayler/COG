#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import unittest
import json
import uuid

import redis

import cogs_api

_REDIS_TESTDB_OFFSET = 1

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
            raise Exception("Test Database Not Empty: {}".format(db.dbsize()))
        self.app = cogs_api.app.test_client()

    def tearDown(self):
        self.db.flushdb()

    def test_root_get(self):
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200, "Bad return status")
        self.assertEqual(res.data, cogs_api._MSG_ROOT, "Data not eqqal")

    def test_create_assignment(self):

        # Create Assignment
        d = {'name': "Test_Assignment_Create",
             'contact': "Andy Sayler"}
        ds = json.dumps(d)
        res = self.app.post('/assignments/', data=ds)
        self.assertEqual(res.status_code, 200, "Bad return status")
        out = json.loads(res.data)
        out_uuid = uuid.UUID(out.keys()[0])
        out_d = out[str(out_uuid)]
        self.assertEqual(d, out_d, "Attributes do not match")

    def test_get_assignment(self):

        # Create Assignment
        d = {'name': "Test_Assignment_Get",
             'contact': "Andy Sayler"}
        ds = json.dumps(d)
        res_a = self.app.post('/assignments/', data=ds)
        self.assertEqual(res_a.status_code, 200, "Bad return status")
        a_dict = json.loads(res_a.data)
        a_uuid = uuid.UUID(a_dict.keys()[0])
        self.assertEqual(d, a_dict[str(a_uuid)], "Attributes do not match")

        # Get Assignment
        res_b = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_b.status_code, 200, "Bad return status")
        b_dict = json.loads(res_b.data)
        b_uuid = uuid.UUID(b_dict.keys()[0])
        self.assertEqual(a_uuid, b_uuid, "UUIDs do not match")
        self.assertEqual(a_dict[str(a_uuid)], b_dict[str(b_uuid)], "Attributes do not match")

    def test_set_assignment(self):

        # Create Assignment
        d_a = {'name': "Test_Assignment_Set_A",
               'contact': "Andy Sayler"}
        ds_a = json.dumps(d_a)
        res_a = self.app.post('/assignments/', data=ds_a)
        self.assertEqual(res_a.status_code, 200, "Bad return status")
        a_dict = json.loads(res_a.data)
        a_uuid = uuid.UUID(a_dict.keys()[0])
        self.assertEqual(d_a, a_dict[str(a_uuid)], "Attributes do not match")

        # Update Assignment
        d_b = {'name': "Test_Assignment_Set_B",
               'contact': "Andy Sayler III"}
        ds_b = json.dumps(d_b)
        res_b = self.app.put('/assignments/{:s}/'.format(a_uuid), data=ds_b)
        self.assertEqual(res_b.status_code, 200, "Bad return status")
        b_dict = json.loads(res_b.data)
        b_uuid = uuid.UUID(b_dict.keys()[0])
        self.assertEqual(a_uuid, b_uuid, "UUIDs do not match")
        self.assertEqual(d_b, b_dict[str(b_uuid)], "Return does not match input")

        # Get Assignment
        res_c = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_c.status_code, 200, "Bad return status")
        c_dict = json.loads(res_c.data)
        c_uuid = uuid.UUID(c_dict.keys()[0])
        self.assertEqual(b_uuid, c_uuid, "UUIDs do not match")
        self.assertEqual(b_dict[str(b_uuid)], c_dict[str(c_uuid)], "Attributes do not match")

    def test_delete_assignment(self):

        # Create Assignment
        d_a = {'name': "Test_Assignment_Delete",
               'contact': "Andy Sayler"}
        ds_a = json.dumps(d_a)
        res_a = self.app.post('/assignments/', data=ds_a)
        self.assertEqual(res_a.status_code, 200, "Bad return status")
        a_dict = json.loads(res_a.data)
        a_uuid = uuid.UUID(a_dict.keys()[0])
        self.assertEqual(d_a, a_dict[str(a_uuid)], "Attributes do not match")

        # Get Assignment
        res_b = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_b.status_code, 200, "Bad return status")
        b_dict = json.loads(res_b.data)
        b_uuid = uuid.UUID(b_dict.keys()[0])
        self.assertEqual(a_uuid, b_uuid, "UUIDs do not match")
        self.assertEqual(a_dict[str(a_uuid)], b_dict[str(b_uuid)], "Attributes do not match")

        # Delete Assignment
        res_c = self.app.delete('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_c.status_code, 200, "Bad return status")

        # Get Assignment
        res_b = self.app.get('/assignments/{:s}/'.format(a_uuid))
        self.assertEqual(res_b.status_code, 404, "Bad return status")

    def test_list_assignments(self):

        assignments_in = set([])

        # Get Assignments (Empty)
        res_a = self.app.get('/assignments/')
        self.assertEqual(res_a.status_code, 200, "Bad return status")
        a_dict = json.loads(res_a.data)
        assignments_out = set(a_dict[cogs_api.datatypes._KEY_ASSIGNMENTS])
        self.assertEqual(assignments_in, assignments_out, "Assignment lists do not match")

        # Create Assignments
        for i in range(10):
            d = {'name': "Test_Assignment_List_{:02d}".format(i),
                   'contact': "Andy Sayler"}
            ds = json.dumps(d)
            res = self.app.post('/assignments/', data=ds)
            self.assertEqual(res.status_code, 200, "Bad return status")
            r_dict = json.loads(res.data)
            r_uuid = uuid.UUID(r_dict.keys()[0])
            self.assertEqual(d, r_dict[str(r_uuid)], "Attributes do not match")
            assignments_in.add(str(r_uuid))

        # Get Assignments
        res_b = self.app.get('/assignments/')
        self.assertEqual(res_b.status_code, 200, "Bad return status")
        b_dict = json.loads(res_b.data)
        assignments_out = set(b_dict[cogs_api.datatypes._KEY_ASSIGNMENTS])
        self.assertEqual(assignments_in, assignments_out, "Assignment lists do not match")

        # Delete Assignments
        for i in range(5):
            r_uuid = assignments_in.pop()
            res_c = self.app.delete('/assignments/{:s}/'.format(r_uuid))
            self.assertEqual(res_c.status_code, 200, "Bad return status")

        # Get Assignments
        res_d = self.app.get('/assignments/')
        self.assertEqual(res_d.status_code, 200, "Bad return status")
        d_dict = json.loads(res_d.data)
        assignments_out = set(d_dict[cogs_api.datatypes._KEY_ASSIGNMENTS])
        self.assertEqual(assignments_in, assignments_out, "Assignment lists do not match")


### Main
if __name__ == '__main__':
    unittest.main()
