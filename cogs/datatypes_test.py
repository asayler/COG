#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import unittest

import redis

import datatypes

_REDIS_TESTDB_OFFSET = 1

class DatatypesTestError(Exception):
    """Base class for Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(DatatypesTestError, self).__init__(*args, **kwargs)

class DatatypesTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        datatypes._REDIS_DB += _REDIS_TESTDB_OFFSET
        db = redis.StrictRedis(host=datatypes._REDIS_HOST,
                               port=datatypes._REDIS_PORT,
                               db=datatypes._REDIS_DB)
        if (db.dbsize() != 0):
            raise DatatypesTestError("Test Database Not Empty: {}".format(db.dbsize()))

    @classmethod
    def tearDownClass(cls):
        db = redis.StrictRedis(host=datatypes._REDIS_HOST,
                               port=datatypes._REDIS_PORT,
                               db=datatypes._REDIS_DB)
        db.flushdb()
        datatypes._REDIS_DB -= _REDIS_TESTDB_OFFSET

    def setUp(self):
        pass

    def tearDown(self):
        pass

class ServerTestCase(DatatypesTestCase):

    def setUp(self):
        super(ServerTestCase, self).setUp()
        self.s = datatypes.Server()

    def tearDown(self):
        del(self.s)
        super(ServerTestCase, self).tearDown()

    def test_assignments_list(self):

        # Generate 10 Assingments
        assignments_in = set([])
        for i in range(10):
            a_dict = {}
            a_dict['name'] = "Test_Assignment_{:02d}"
            a_dict['contact'] = "Andy Sayler"
            assignments_in.add(repr(datatypes.Assignment.from_new(a_dict)))

        # List Assignments
        assignments_out = self.s.assignments_list()

        # Verify Assignments
        self.assertEqual(assignments_in, assignments_out, "Assignment Sets Differ")

if __name__ == '__main__':
    unittest.main()
