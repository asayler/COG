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
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        datatypes._REDIS_DB += _REDIS_TESTDB_OFFSET
        self.db = redis.StrictRedis(host=datatypes._REDIS_HOST,
                                    port=datatypes._REDIS_PORT,
                                    db=datatypes._REDIS_DB)
        if (self.db.dbsize() != 0):
            raise DatatypesTestError("Test Database Not Empty: {}".format(db.dbsize()))

    def tearDown(self):
        self.db.flushdb()
        datatypes._REDIS_DB -= _REDIS_TESTDB_OFFSET

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

    def test_get_dict(self):
        # Generate 10 Assingments
        for i in range(10):
            d_in = {}
            d_in['name'] = "Test_Assignment_{:02d}".format(i)
            d_in['contact'] = "Andy Sayler"
            a = datatypes.Assignment.from_new(d_in)
            d_out = a.get_dict()
            # Test Equal
            self.assertEqual(d_in, d_out)

    def test_set_dict(self):
        # Generate 10 Assingments
        for i in range(10):
            d_1 = {}
            d_1['name'] = "Test_Assignment_{:02d}".format(i)
            d_1['contact'] = "Andy Sayler"
            a = datatypes.Assignment.from_new(d_1)
            self.assertEqual(d_1, a.get_dict())
            d_2 = {}
            d_2['name'] = "Test_Assignment_Updated".format(i)
            d_2['contact'] = "Andy Sayler the 3rd"
            a.set_dict(d_2)
            # Test Equal
            self.assertEqual(d_2, a.get_dict())

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

        assignments_in = set([])

        # List Assignments (Empty DB)
        assignments_out = self.s.assignments_list()
        self.assertEqual(assignments_in, assignments_out, "Assignment Sets Differ")

        # Generate 10 Assingments
        for i in range(10):
            a_dict = {}
            a_dict['name'] = "Test_Assignment_{:02d}".format(i)
            a_dict['contact'] = "Andy Sayler"
            assignments_in.add(repr(datatypes.Assignment.from_new(a_dict)))

        # List Assignments
        assignments_out = self.s.assignments_list()
        self.assertEqual(assignments_in, assignments_out, "Assignment Sets Differ")


# Main
if __name__ == '__main__':
    unittest.main()
