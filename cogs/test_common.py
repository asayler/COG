#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import os
import unittest

import redis

# Set Test Struct Create Data
DUMMY_SCHEMA   = ['key1', 'key2', 'key3']
DUMMY_TESTDICT = {'key1': "val1",
                  'key2': "val2",
                  'key3': "val3"}
USER_TESTDICT = {}
GROUP_TESTDICT = {'name': "testgroup"}
FILE_TESTDICT  = {'key': "Test_File"}
ASSIGNMENT_TESTDICT = {'name': "Test_Assignment", 'env': "local"}
TEST_TESTDICT = {'name': "Test_Assignment",
                 'maxscore': "10",
                 'tester': "script"}
SUBMISSION_TESTDICT = {}

# Set Default Vals
MOD_PATH = os.path.dirname(os.path.realpath(__file__))
TOP_PATH = os.path.realpath("{:s}/..".format(MOD_PATH))
TEST_INPUT_PATH = os.path.realpath("{:s}/test_input".format(TOP_PATH))
TEST_REDIS_HOST = "localhost"
TEST_REDIS_PORT = 6379
TEST_REDIS_DB = 5

# Get Test Vars
TEST_INPUT_PATH = os.environ.get('COGS_TEST_INPUT_PATH', TEST_INPUT_PATH)
MOODLE_USERNAME = os.environ.get('COGS_TEST_MOODLE_USERNAME', 'moodleuser')
MOODLE_PASSWORD = os.environ.get('COGS_TEST_MOODLE_PASSWORD', 'moodlepass')
ADMIN_AUTHMOD = os.environ.get('COGS_TEST_ADMIN_AUTHMOD', 'test')
ADMIN_USERNAME = os.environ.get('COGS_TEST_ADMIN_USERNAME', 'adminuser')
ADMIN_PASSWORD = os.environ.get('COGS_TEST_ADMIN_PASSWORD', 'adminpass')
REDIS_HOST = os.environ.get('COGS_TEST_REDIS_HOST', TEST_REDIS_HOST)
REDIS_PORT = int(os.environ.get('COGS_TEST_REDIS_PORT', TEST_REDIS_PORT))
REDIS_DB = int(os.environ.get('COGS_TEST_REDIS_DB', TEST_REDIS_DB))

# Set DB Vars
os.environ['COGS_REDIS_HOST'] = REDIS_HOST
os.environ['COGS_REDIS_PORT'] = str(REDIS_PORT)
os.environ['COGS_REDIS_DB'] = str(REDIS_DB)

# Create DB
db = redis.StrictRedis(host=REDIS_HOST,
                       port=REDIS_PORT,
                       db=REDIS_DB)


class CogsTestError(Exception):
    """Base class for Cogs Test Exceptions"""

    def __init__(self, *args, **kwargs):
        super(CogsTestError, self).__init__(*args, **kwargs)


class CogsTestCase(unittest.TestCase):

    def setUp(self):
        self.db = db
        if (self.db.dbsize() != 0):
            raise CogsTestError("Test Database Not Empty: {}".format(self.db.dbsize()))

    def tearDown(self):
        self.db.flushdb()

    def assertSubset(self, sub, sup):

        if type(sub) != type(sup):
            raise CogsTestError("sub, sup must be of same type")

        if type(sub) == dict:
            for k in sub:
                self.assertEqual(sub[k], sup[k])
        elif type(sub) == set:
            self.assertTrue(sub.issubset(sup))
        elif type(sub) == list:
            self.assertTrue(set(sub).issubset(set(sup)))
        else:
            raise CogsTestError("Unhandled type: {:s}".format(type(sub)))
