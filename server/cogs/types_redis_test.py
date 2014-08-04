#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import random
import unittest

import redis

import types_redis
import test_common


class DatatypesTestCase(test_common.CogsTestCase):

    def setUp(self):
        super(DatatypesTestCase, self).setUp()

    def tearDown(self):
        super(DatatypesTestCase, self).tearDown()


class RedisFactoryTestCase(DatatypesTestCase):

    def setUp(self):
        super(RedisFactoryTestCase, self).setUp()

    def tearDown(self):
        super(RedisFactoryTestCase, self).tearDown()

    def test_init(self):

        # Test w/o Prefix or Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        hf = types_redis.RedisFactory(types_redis.RedisHashBase, redis_db=self.db)
        self.assertRaises(types_redis.RedisObjectError, hf.from_new, d)

        # Test w/ Prefix but w/o Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        p = "test_prefix_{:03d}".format(random.randint(0, 999))
        hf = types_redis.RedisFactory(types_redis.RedisHashBase, prefix=p, redis_db=self.db)
        h = hf.from_new(d)
        self.assertSubset(d, h.get_dict())

        # Test w/ Key but w/o Prefix
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        k = "test_key_{:03d}".format(random.randint(0, 999))
        hf = types_redis.RedisFactory(types_redis.RedisHashBase, redis_db=self.db)
        h = hf.from_new(d, k)
        self.assertSubset(d, h.get_dict())

        # Test w/ Prefix and Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        p = "test_prefix_{:03d}".format(random.randint(0, 999))
        k = "test_key_{:03d}".format(random.randint(0, 999))
        hf = types_redis.RedisFactory(types_redis.RedisHashBase, prefix=p, redis_db=self.db)
        h = hf.from_new(d, k)
        self.assertSubset(d, h.get_dict())


class RedisHashTestCase(DatatypesTestCase):

    def setUp(self):
        super(RedisHashTestCase, self).setUp()

        self.HashFactory = types_redis.RedisFactory(types_redis.RedisHashBase, redis_db=self.db)

    def tearDown(self):
        super(RedisHashTestCase, self).tearDown()

    def test_from_new(self):

        # Create Key
        k = "test_key_{:03d}".format(random.randint(0, 999))

        # Test Empty Dict w/o Key
        d = {}
        self.assertRaises(types_redis.RedisObjectError, self.HashFactory.from_new, d)

        # Test Empty Dict w/ Key
        d = {}
        self.assertRaises(types_redis.RedisObjectError, self.HashFactory.from_new, d, k)

        # Test Non-Empty Dict w/o Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        self.assertRaises(types_redis.RedisObjectError, self.HashFactory.from_new, d)

        # Test Non-Empty Dict w Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h = self.HashFactory.from_new(d, k)
        self.assertSubset(d, h.get_dict())

    def test_from_existing(self):

        # Create Key
        k = "test_key_{:03d}".format(random.randint(0, 999))

        # Test Non-Existant Object
        self.assertRaises(types_redis.RedisObjectDNE, self.HashFactory.from_existing, k)

        # Test Existing Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h1 = self.HashFactory.from_new(d, k)
        h2 = self.HashFactory.from_existing(k)
        self.assertEqual(h1, h2)

    def test_get_dict(self):

        # Create Key
        k = "test_key_{:03d}".format(random.randint(0, 999))

        # Create and Get Object
        d_in = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d_in, k)
        d_out = obj.get_dict()
        self.assertSubset(d_in, d_out)

    def test_set_dict(self):

        # Create Key
        k = "test_key_{:03d}".format(random.randint(0, 999))

        # Create and Get Object
        d1_in = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d1_in, k)
        d1_out = obj.get_dict()
        self.assertSubset(d1_in, d1_out)

        # Update and Get Object
        d2_in = copy.deepcopy(test_common.DUMMY_TESTDICT)
        for k in d2_in:
            d2_in[k] = "set_dict_test_val_{:s}".format(k)
        self.assertNotEqual(d1_in, d2_in)
        obj.set_dict(d2_in)
        d2_out = obj.get_dict()
        self.assertSubset(d2_in, d2_out)

    def test_getitem(self):

        # Temp Get Funcation
        def get_item(d, key):
            return d[key]

        # Create Object Key
        k = "test_key_{:03d}".format(random.randint(0, 999))

        # Create Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d, k)

        # Test Bad Key
        self.assertRaises(KeyError, get_item, obj, 'test')

        # Test Good Keys
        for key in d:
            self.assertEqual(d[key], obj[key])

    def test_setitem(self):

        # Temp Set Function
        def set_item(d, key, val):
            d[key] = val

        # Create Object Key
        k = "test_key_{:03d}".format(random.randint(0, 999))

        # Create Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d, k)

        # Test Keys
        for key in d:
            val = d[key] + "_updated"
            obj[key] = val
            self.assertEqual(val, obj[key])


### Main ###
if __name__ == '__main__':
    unittest.main()
