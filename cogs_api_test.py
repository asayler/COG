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
        d = {'name': "Test_Assignment_Create",
             'contact': "Andy Sayler"}
        ds = json.dumps(d)
        res = self.app.post('/assignments/', data=ds)
        out = json.loads(res.data)
        out_uuid = uuid.UUID(out.keys()[0])
        out_d = out[str(out_uuid)]
        self.assertEqual(d, out_d, "Return does not match input")

    def test_create_assignment(self):
        d = {'name': "Test_Assignment_Create",
             'contact': "Andy Sayler"}
        ds = json.dumps(d)
        res = self.app.post('/assignments/', data=ds)
        out = json.loads(res.data)
        out_uuid = uuid.UUID(out.keys()[0])
        out_d = out[str(out_uuid)]
        self.assertEqual(d, out_d, "Return does not match input")


### Main
if __name__ == '__main__':
    unittest.main()
