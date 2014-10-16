#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import os
import unittest

import redis

import config


# Set Test Struct Create Data
DUMMY_SCHEMA   = ['key1', 'key2', 'key3']
DUMMY_TESTDICT = {'key1': "val1",
                  'key2': "val2",
                  'key3': "val3"}
USER_TESTDICT = {}
GROUP_TESTDICT = {'name': "testgroup"}
FILE_TESTDICT  = {'key': "testfile"}
REPORTER_TESTDICT  = {'mod': "moodle"}
ASSIGNMENT_TESTDICT = {'name': "Test_Assignment", 'env': "local"}
TEST_TESTDICT = {'name': "Test_Assignment",
                 'maxscore': "10",
                 'tester': "script"}
SUBMISSION_TESTDICT = {}
RUN_TESTDICT = {}

# Set Local Default Vals
TEST_INPUT_PATH = os.path.realpath("{:s}/test_input".format(config.ROOT_PATH))
TEST_AUTHMOD_MOODLE_STUDENT_USERNAME = None
TEST_AUTHMOD_MOODLE_STUDENT_PASSWORD = None
TEST_REPMOD_MOODLE_ASN = "1"
TEST_ADMIN_AUTHMOD = "test"
TEST_ADMIN_USERNAME = "testadmin"
TEST_ADMIN_PASSWORD = "testpassword"
TEST_MOODLE_HOST = "https://moodle-test.cs.colorado.edu"
TEST_MOODLE_SERVICE = "Grading_Serv"

# Set Override Default Vals
TEST_REDIS_DB = 5
TEST_LOGGING_ENABLED = "False"
TEST_FILESTORAGE_PATH = "/tmp/cog_test/files"
TEST_ARCHIVE_PATH = "/tmp/cog_test/archives"
TEST_UPLOAD_PATH = "/tmp/cog_test/uploads"
TEST_ENV_LOCAL_TMP_PATH = "/tmp/cog_test/envs"
TEST_AUTHMOD_MOODLE_HOST = TEST_MOODLE_HOST
TEST_AUTHMOD_MOODLE_SERVICE = TEST_MOODLE_SERVICE
TEST_REPMOD_MOODLE_HOST = TEST_MOODLE_HOST
TEST_REPMOD_MOODLE_SERVICE = TEST_MOODLE_SERVICE
TEST_REPMOD_MOODLE_USERNAME = None
TEST_REPMOD_MOODLE_PASSWORD = None
TEST_ENV_LOCAL_LIMIT_TIME_CPU = "1"
TEST_ENV_LOCAL_LIMIT_TIME_WALL = "3"

# Get Local Test Env Vars
TEST_INPUT_PATH = os.environ.get('COGS_TEST_INPUT_PATH', TEST_INPUT_PATH)
if TEST_AUTHMOD_MOODLE_STUDENT_USERNAME:
    AUTHMOD_MOODLE_STUDENT_USERNAME = os.environ.get('COGS_TEST_AUTHMOD_MOODLE_STUDENT_USERNAME',
                                                     TEST_AUTHMOD_MOODLE_STUDENT_USERNAME)
else:
    AUTHMOD_MOODLE_STUDENT_USERNAME = os.environ['COGS_TEST_AUTHMOD_MOODLE_STUDENT_USERNAME']
if TEST_AUTHMOD_MOODLE_STUDENT_PASSWORD:
    AUTHMOD_MOODLE_STUDENT_PASSWORD = os.environ.get('COGS_TEST_AUTHMOD_MOODLE_STUDENT_PASSWORD',
                                                     TEST_AUTHMOD_MOODLE_STUDENT_PASSWORD)
else:
    AUTHMOD_MOODLE_STUDENT_PASSWORD = os.environ['COGS_TEST_AUTHMOD_MOODLE_STUDENT_PASSWORD']
ADMIN_AUTHMOD = os.environ.get('COGS_TEST_ADMIN_AUTHMOD', TEST_ADMIN_AUTHMOD)
ADMIN_USERNAME = os.environ.get('COGS_TEST_ADMIN_USERNAME', TEST_ADMIN_USERNAME)
ADMIN_PASSWORD = os.environ.get('COGS_TEST_ADMIN_PASSWORD', TEST_ADMIN_PASSWORD)
REPMOD_MOODLE_ASN = os.environ.get('COGS_TEST_REPMOD_MOODLE_ASN', TEST_REPMOD_MOODLE_ASN)

# Get Override Test Env Vars
REDIS_DB = int(os.environ.get('COGS_TEST_REDIS_DB', TEST_REDIS_DB))
FILESTORAGE_PATH = os.environ.get('COGS_TEST_FILESTORAGE_PATH', TEST_FILESTORAGE_PATH)
ARCHIVE_PATH = os.environ.get('COGS_TEST_ARCHIVE_PATH', TEST_ARCHIVE_PATH)
UPLOAD_PATH = os.environ.get('COGS_TEST_UPLOAD_PATH', TEST_UPLOAD_PATH)
AUTHMOD_MOODLE_HOST = os.environ.get('COGS_TEST_AUTHMOD_MOODLE_HOST', TEST_AUTHMOD_MOODLE_HOST)
AUTHMOD_MOODLE_SERVICE = os.environ.get('COGS_TEST_AUTHMOD_MOODLE_SERVICE', TEST_AUTHMOD_MOODLE_SERVICE)
REPMOD_MOODLE_HOST = os.environ.get('COGS_TEST_REPMOD_MOODLE_HOST', TEST_REPMOD_MOODLE_HOST)
REPMOD_MOODLE_SERVICE = os.environ.get('COGS_TEST_REPMOD_MOODLE_SERVICE', TEST_REPMOD_MOODLE_SERVICE)
if TEST_REPMOD_MOODLE_USERNAME:
    REPMOD_MOODLE_USERNAME = os.environ.get('COGS_TEST_REPMOD_MOODLE_USERNAME',
                                            TEST_REPMOD_MOODLE_USERNAME)
else:
    REPMOD_MOODLE_USERNAME = os.environ['COGS_TEST_REPMOD_MOODLE_USERNAME']
if TEST_REPMOD_MOODLE_PASSWORD:
    REPMOD_MOODLE_PASSWORD = os.environ.get('COGS_TESTREPMOD_MOODLE_PASSWORD',
                                            TEST_REPMOD_MOODLE_PASSWORD)
else:
    REPMOD_MOODLE_PASSWORD = os.environ['COGS_TEST_REPMOD_MOODLE_PASSWORD']

# Set Override DB Vars
os.environ['COGS_REDIS_DB'] = str(REDIS_DB)
os.environ['COGS_FILESTORAGE_PATH'] = FILESTORAGE_PATH
os.environ['COGS_ARCHIVE_PATH'] = ARCHIVE_PATH
os.environ['COGS_UPLOAD_PATH'] = UPLOAD_PATH
os.environ['COGS_ENV_LOCAL_TMP_PATH'] = TEST_ENV_LOCAL_TMP_PATH
os.environ['COGS_LOGGING_ENABLED'] = TEST_LOGGING_ENABLED
os.environ['COGS_AUTHMOD_MOODLE_HOST'] = AUTHMOD_MOODLE_HOST
os.environ['COGS_AUTHMOD_MOODLE_SERVICE'] = AUTHMOD_MOODLE_SERVICE
os.environ['COGS_REPMOD_MOODLE_HOST'] = REPMOD_MOODLE_HOST
os.environ['COGS_REPMOD_MOODLE_SERVICE'] = REPMOD_MOODLE_SERVICE
os.environ['COGS_REPMOD_MOODLE_USERNAME'] = REPMOD_MOODLE_USERNAME
os.environ['COGS_REPMOD_MOODLE_PASSWORD'] = REPMOD_MOODLE_PASSWORD
os.environ['COGS_ENV_LOCAL_LIMIT_TIME_CPU'] = TEST_ENV_LOCAL_LIMIT_TIME_CPU
os.environ['COGS_ENV_LOCAL_LIMIT_TIME_WALL'] = TEST_ENV_LOCAL_LIMIT_TIME_WALL

reload(config)

# Create DB
db = redis.StrictRedis(host=config.REDIS_HOST,
                       port=config.REDIS_PORT,
                       db=config.REDIS_DB,
                       password=config.REDIS_PASSWORD)


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
                self.assertEqual(str(sub[k]), str(sup[k]))
        elif type(sub) == set:
            self.assertTrue(sub.issubset(sup))
        elif type(sub) == list:
            self.assertTrue(set(sub).issubset(set(sup)))
        else:
            raise CogsTestError("Unhandled type: {:s}".format(type(sub)))
