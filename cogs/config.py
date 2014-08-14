# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os

# Set Paths
MOD_PATH = os.path.dirname(os.path.realpath(__file__))
ROOT_PATH = os.path.realpath("{:s}/..".format(MOD_PATH))

# Set Default Vals
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 4
DEFAULT_REDIS_PASSWORD = None
DEFAULT_SCRIPT_PATH = os.path.realpath("{:s}/scripts".format(ROOT_PATH))
DEFAULT_GRADER_MOODLE_USERNAME = None
DEFAULT_GRADER_MOODLE_PASSWORD = None

# Get Env Vars
SCRIPT_PATH = os.environ.get('COGS_SCRIPT_PATH', DEFAULT_SCRIPT_PATH)
REDIS_HOST = os.environ.get('COGS_REDIS_HOST', DEFAULT_REDIS_HOST)
REDIS_PORT = int(os.environ.get('COGS_REDIS_PORT', DEFAULT_REDIS_PORT))
REDIS_DB = int(os.environ.get('COGS_REDIS_DB', DEFAULT_REDIS_DB))
REDIS_PASSWORD = os.environ.get('COGS_REDIS_PASSWORD', DEFAULT_REDIS_PASSWORD)
GRADER_MOODLE_USERNAME = os.environ.get('COGS_GRADER_MOODLE_USERNAME', DEFAULT_GRADER_MOODLE_USERNAME)
GRADER_MOODLE_PASSWORD = os.environ.get('COGS_GRADER_MOODLE_PASSWORD', DEFAULT_GRADER_MOODLE_PASSWORD)
