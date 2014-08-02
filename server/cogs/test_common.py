#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import unittest

import redis


_REDIS_CONF_TEST = {'redis_host': "localhost",
                    'redis_port': 6379,
                    'redis_db': 5}

DUMMY_SCHEMA         = ['key1', 'key2', 'key3']
DUMMY_TESTDICT       = {'key1': "val1",
                        'key2': "val2",
                        'key3': "val3"}

ASSIGNMENT_TESTDICT  = {'name': "Test_Assignment",
                        'contact': "Andy Sayler",
                        'permissions': '01c47915-4777-11d8-bc70-0090272ff725'}

TEST_TESTDICT        = {'name': "Test_Assignment",
                        'contact': "Andy Sayler",
                        'type': "script",
                        'maxscore': "10"}


class CogsTestError(Exception):
    """Base class for COgs Test Exceptions"""

    def __init__(self, *args, **kwargs):
        super(CogsTestError, self).__init__(*args, **kwargs)


class CogsTestCase(unittest.TestCase):

    def setUp(self):
        self.db = redis.StrictRedis(host=_REDIS_CONF_TEST['redis_host'],
                                    port=_REDIS_CONF_TEST['redis_port'],
                                    db=_REDIS_CONF_TEST['redis_db'])
        if (self.db.dbsize() != 0):
            raise CogsTestError("Test Database Not Empty: {}".format(self.db.dbsize()))

    def tearDown(self):
        self.db.flushdb()

    def assertSubset(self, sub, sup):
        for k in sub:
            self.assertEqual(sub[k], sup[k])
