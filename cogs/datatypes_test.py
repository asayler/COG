#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import unittest

import redis

import datatypes

_REDIS_TESTDB_OFFSET = 1

_UUIDREDISOBJECT_TESTDICT = {'key1': "val1",
                             'key2': "val2",
                             'key3': "val3"}
_ASSIGNMENT_TESTDICT      = {'name': "Test_Assignment",
                             'contact': "Andy Sayler"}
_ASSIGNMENTTEST_TESTDICT  = {'name': "Test_Assignment",
                             'contact': "Andy Sayler",
                             'path': "/tmp/test.py",
                             'maxscore': 10}


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


class UUIDRedisObjectTestCase(DatatypesTestCase):

    def setUp(self):
        super(UUIDRedisObjectTestCase, self).setUp()

    def tearDown(self):
        super(UUIDRedisObjectTestCase, self).tearDown()

    def test_from_new(self):

        # Test Empty Dict
        d = {}
        self.assertRaises(KeyError, datatypes.UUIDRedisObject.from_new, d)

        # Test Bad Dict
        d = {'test': "test"}
        self.assertRaises(KeyError, datatypes.UUIDRedisObject.from_new, d)

        # Test Sub Dict
        d = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        d.pop(d.keys()[0])
        self.assertRaises(KeyError, datatypes.UUIDRedisObject.from_new, d)

        # Test Super Dict
        d = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        d['test'] = "test"
        self.assertRaises(KeyError, datatypes.UUIDRedisObject.from_new, d)

        # Test Valid
        d = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        a = datatypes.UUIDRedisObject.from_new(d)

    def test_from_existing(self):

        # Test Invalid UUID
        self.assertRaises(datatypes.UUIDRedisObjectDNE,
                          datatypes.UUIDRedisObject.from_existing,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf')

        # Test Valid UUID
        d = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        obj1 = datatypes.UUIDRedisObject.from_new(d)
        obj1_uuid = repr(obj1)
        obj2 = datatypes.UUIDRedisObject.from_existing(obj1_uuid)
        self.assertEqual(obj1, obj2)

    def test_get_dict(self):

        # Create and Get Object
        d_in = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        obj = datatypes.UUIDRedisObject.from_new(d_in)
        d_out = obj.get_dict()
        self.assertEqual(d_in, d_out)

    def test_set_dict(self):

        # Create and Get Object
        d1_in = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        obj = datatypes.UUIDRedisObject.from_new(d1_in)
        d1_out = obj.get_dict()
        self.assertEqual(d1_in, d1_out)

        # Update and Get Object
        d2_in = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        for k in d2_in:
            d2_in[k] = "set_dict_test_val_{:s}".format(k)
        self.assertNotEqual(d1_in, d2_in)
        obj.set_dict(d2_in)
        d2_out = obj.get_dict()
        self.assertEqual(d2_in, d2_out)

    def test_getitem(self):

        # Temp Get Funcation
        def get_item(d, k):
            return d[k]

        # Test Good Keys
        d = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        obj = datatypes.UUIDRedisObject.from_new(d)
        for k in d:
            self.assertEqual(d[k], obj[k])

        # Test Bad Key
        self.assertRaises(KeyError, get_item, obj, 'test')

    def test_setitem(self):

        # Temp Set Function
        def set_item(d, k, v):
            d[k] = v

        # Test Good Keys
        d = copy.deepcopy(_UUIDREDISOBJECT_TESTDICT)
        obj = datatypes.UUIDRedisObject.from_new(d)
        for k in d:
            val = d[k] + "_updated"
            obj[k] = val
            self.assertEqual(val, obj[k])

        # Test Bad Key
        self.assertRaises(KeyError, set_item, obj, 'test', "test")


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
