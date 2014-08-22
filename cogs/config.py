# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import ConfigParser
import os

config = ConfigParser.SafeConfigParser(allow_no_value=True)

# Sections
SEC_REDIS = "redis"
config.add_section(SEC_REDIS)
SEC_FILESTORAGE = "filestorage"
config.add_section(SEC_FILESTORAGE)

# Set Paths
MOD_PATH = os.path.dirname(os.path.realpath(__file__))
ROOT_PATH = os.path.realpath("{:s}/..".format(MOD_PATH))
CONF_PATH = os.path.realpath("{:s}/{:s}".format(ROOT_PATH, "cog.conf"))

# Set Default Vals
config.set(SEC_REDIS, 'HOST', "localhost")
config.set(SEC_REDIS, 'PORT', "6379")
config.set(SEC_REDIS, 'DB', "4")
config.set(SEC_REDIS, 'PASSWORD', None)
config.set(SEC_FILESTORAGE, 'PATH', "{:s}/files".format(ROOT_PATH))
DEFAULT_SCRIPT_PATH = os.path.realpath("{:s}/scripts".format(ROOT_PATH))
DEFAULT_ENV_LOCAL_TMP_PATH = "/tmp/cogs"
DEFAULT_ENV_LOCAL_SANDBOX = "local_sandbox.py"
DEFAULT_TESTER_SCRIPT_USER = "nobody"
DEFAULT_TESTER_SCRIPT_GROUP = "nogroup"
DEFAULT_AUTHMOD_MOODLE_HOST = None
DEFAULT_AUTHMOD_MOODLE_SERVICE = None
DEFAULT_REPMOD_MOODLE_HOST = None
DEFAULT_REPMOD_MOODLE_SERVICE = None
DEFAULT_REPMOD_MOODLE_USERNAME = None
DEFAULT_REPMOD_MOODLE_PASSWORD = None

# Read Config File
config.read(CONF_PATH)

# Get Env Var Overrides
REDIS_HOST = os.environ.get('COGS_REDIS_HOST', config.get(SEC_REDIS, 'HOST'))
REDIS_PORT = int(os.environ.get('COGS_REDIS_PORT', config.get(SEC_REDIS, 'PORT')))
REDIS_DB = int(os.environ.get('COGS_REDIS_DB', config.get(SEC_REDIS, 'DB')))
REDIS_PASSWORD = os.environ.get('COGS_REDIS_PASSWORD', config.get(SEC_REDIS, 'PASSWORD'))
FILESTORAGE_PATH = os.path.realpath(os.environ.get('COGS_FILESTORAGE_PATH',
                                                   config.get(SEC_FILESTORAGE, 'PATH')))
SCRIPT_PATH = os.environ.get('COGS_SCRIPT_PATH', DEFAULT_SCRIPT_PATH)
ENV_LOCAL_TMP_PATH = os.environ.get('COGS_ENV_LOCAL_TMP_PATH', DEFAULT_ENV_LOCAL_TMP_PATH)
ENV_LOCAL_SANDBOX = os.environ.get('COGS_ENV_LOCAL_SANDBOX', DEFAULT_ENV_LOCAL_SANDBOX)
TESTER_SCRIPT_USER = os.environ.get('COGS_TESTER_SCRIPT_USER', DEFAULT_TESTER_SCRIPT_USER)
TESTER_SCRIPT_GROUP = os.environ.get('COGS_TESTER_SCRIPT_GROUP', DEFAULT_TESTER_SCRIPT_GROUP)
AUTHMOD_MOODLE_HOST = os.environ.get('COGS_AUTHMOD_MOODLE_HOST', DEFAULT_AUTHMOD_MOODLE_HOST)
AUTHMOD_MOODLE_SERVICE = os.environ.get('COGS_AUTHMOD_MOODLE_SERVICE', DEFAULT_AUTHMOD_MOODLE_SERVICE)
REPMOD_MOODLE_HOST = os.environ.get('COGS_REPMOD_MOODLE_HOST', DEFAULT_REPMOD_MOODLE_HOST)
REPMOD_MOODLE_SERVICE = os.environ.get('COGS_REPMOD_MOODLE_SERVICE', DEFAULT_REPMOD_MOODLE_SERVICE)
REPMOD_MOODLE_USERNAME = os.environ.get('COGS_REPMOD_MOODLE_USERNAME', DEFAULT_REPMOD_MOODLE_USERNAME)
REPMOD_MOODLE_PASSWORD = os.environ.get('COGS_REPMOD_MOODLE_PASSWORD', DEFAULT_REPMOD_MOODLE_PASSWORD)
