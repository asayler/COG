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

class AssignmentTestCase(DatatypesTestCase):

    def setUp(self):
        super(AssignmentTestCase, self).setUp()

    def tearDown(self):
        super(AssignmentTestCase, self).tearDown()

    def test_from_new(self):

        # Test Empty Dict
        d = {}
        self.assertRaises(KeyError, datatypes.Assignment.from_new, d)

        # Test Bad Dict
        d = {'test': "test"}
        self.assertRaises(KeyError, datatypes.Assignment.from_new, d)

        # Test Sub Dict
        d = {'name': "Test_Assignment"}
        self.assertRaises(KeyError, datatypes.Assignment.from_new, d)

        # Test Supper Dict
        d = {'name': "Test_Assignment",
             'contact': "Andy Sayler",
             'Test': 'Test'}
        self.assertRaises(KeyError, datatypes.Assignment.from_new, d)

        # Test Valid
        d = {'name': "Test_Assignment",
             'contact': "Andy Sayler"}
        a = datatypes.Assignment.from_new(d)

    def test_from_existing(self):

        # Test Invalid UUID
        self.assertRaises(datatypes.UUIDRedisObjectDNE,
                          datatypes.Assignment.from_existing,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf')

        # Test Valid UUID
        d = {'name': "Test_Assignment",
             'contact': "Andy Sayler"}
        a1 = datatypes.Assignment.from_new(d)
        a2_uuid = repr(a1)
        a2 = datatypes.Assignment.from_existing(a2_uuid)
        self.assertEqual(a1, a2)

    def test_getitem(self):

        def get_item(d, k):
            return d[k]

        # Generate 10 Assingments
        for i in range(10):
            d = {}
            d['name'] = "Test_Assignment_{:02d}".format(i)
            d['contact'] = "Andy Sayler"
            a = datatypes.Assignment.from_new(d)
            # Test Equal
            self.assertEqual(a['name'], d['name'])
            self.assertEqual(a['contact'], d['contact'])
            # Test Bad Key
            self.assertRaises(KeyError, get_item, a, 'test')

    def test_setitem(self):

        def set_item(d, k, v):
            d[k] = v

        # Generate 10 Assingments
        for i in range(10):
            d = {}
            d['name'] = "Test_Assignment_{:02d}".format(i)
            d['contact'] = "Andy Sayler"
            a = datatypes.Assignment.from_new(d)
            a['name'] = "Test_Assignment"
            a['contact'] = "Nobody"
            # Test Equal
            self.assertEqual(a['name'], "Test_Assignment")
            self.assertEqual(a['contact'], "Nobody")
            # Test Bad Key
            self.assertRaises(KeyError, set_item, a, 'test', 'test')


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
            a_dict['name'] = "Test_Assignment_{:02d}".format(i)
            a_dict['contact'] = "Andy Sayler"
            assignments_in.add(repr(datatypes.Assignment.from_new(a_dict)))

        # List Assignments
        assignments_out = self.s.assignments_list()

        # Verify Assignments
        self.assertEqual(assignments_in, assignments_out, "Assignment Sets Differ")


# Main
if __name__ == '__main__':
    unittest.main()
