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
SEC_LOGGING = "logging"
config.add_section(SEC_LOGGING)
SEC_REPMOD_MOODLE = "repmod_moodle"
config.add_section(SEC_REPMOD_MOODLE)
SEC_AUTHMOD_MOODLE = "authmod_moodle"
config.add_section(SEC_AUTHMOD_MOODLE)

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
config.set(SEC_LOGGING, 'ENABLED', "True")
config.set(SEC_AUTHMOD_MOODLE, 'HOST', None)
config.set(SEC_AUTHMOD_MOODLE, 'SERVICE', None)
config.set(SEC_REPMOD_MOODLE, 'HOST', None)
config.set(SEC_REPMOD_MOODLE, 'SERVICE', None)
config.set(SEC_REPMOD_MOODLE, 'USERNAME', None)
config.set(SEC_REPMOD_MOODLE, 'PASSWORD', None)
DEFAULT_SCRIPT_PATH = os.path.realpath("{:s}/scripts".format(ROOT_PATH))
DEFAULT_ENV_LOCAL_TMP_PATH = "/tmp/cogs"
DEFAULT_ARCHIVE_PATH = "/tmp/cogs/archives"
DEFAULT_ENV_LOCAL_SANDBOX = "local_sandbox.py"
DEFAULT_TESTER_SCRIPT_USER = "nobody"
DEFAULT_TESTER_SCRIPT_GROUP = "nogroup"

# Read Config File
config.read(CONF_PATH)

# Get Env Var Overrides
REDIS_HOST = os.environ.get('COGS_REDIS_HOST', config.get(SEC_REDIS, 'HOST'))
REDIS_PORT = int(os.environ.get('COGS_REDIS_PORT', config.get(SEC_REDIS, 'PORT')))
REDIS_DB = int(os.environ.get('COGS_REDIS_DB', config.get(SEC_REDIS, 'DB')))
REDIS_PASSWORD = os.environ.get('COGS_REDIS_PASSWORD', config.get(SEC_REDIS, 'PASSWORD'))
FILESTORAGE_PATH = os.environ.get('COGS_FILESTORAGE_PATH', config.get(SEC_FILESTORAGE, 'PATH'))
FILESTORAGE_PATH = os.path.realpath(FILESTORAGE_PATH)
ARCHIVE_PATH = os.path.realpath(DEFAULT_ARCHIVE_PATH)
LOGGING_ENABLED = os.environ.get('COGS_LOGGING_ENABLED', config.get(SEC_LOGGING, 'ENABLED'))
LOGGING_ENABLED = LOGGING_ENABLED.lower() in ['true', 'yes', 'on', '1']
AUTHMOD_MOODLE_HOST = os.environ.get('COGS_AUTHMOD_MOODLE_HOST',
                                     config.get(SEC_AUTHMOD_MOODLE, 'HOST'))
AUTHMOD_MOODLE_SERVICE = os.environ.get('COGS_AUTHMOD_MOODLE_SERVICE',
                                        config.get(SEC_AUTHMOD_MOODLE, 'SERVICE'))
REPMOD_MOODLE_HOST = os.environ.get('COGS_REPMOD_MOODLE_HOST',
                                    config.get(SEC_REPMOD_MOODLE, 'HOST'))
REPMOD_MOODLE_SERVICE = os.environ.get('COGS_REPMOD_MOODLE_SERVICE',
                                       config.get(SEC_REPMOD_MOODLE, 'SERVICE'))
REPMOD_MOODLE_USERNAME = os.environ.get('COGS_REPMOD_MOODLE_USERNAME',
                                        config.get(SEC_REPMOD_MOODLE, 'USERNAME'))
REPMOD_MOODLE_PASSWORD = os.environ.get('COGS_REPMOD_MOODLE_PASSWORD',
                                        config.get(SEC_REPMOD_MOODLE, 'PASSWORD'))

SCRIPT_PATH = os.environ.get('COGS_SCRIPT_PATH', DEFAULT_SCRIPT_PATH)
ENV_LOCAL_TMP_PATH = os.environ.get('COGS_ENV_LOCAL_TMP_PATH', DEFAULT_ENV_LOCAL_TMP_PATH)
ENV_LOCAL_SANDBOX = os.environ.get('COGS_ENV_LOCAL_SANDBOX', DEFAULT_ENV_LOCAL_SANDBOX)
TESTER_SCRIPT_USER = os.environ.get('COGS_TESTER_SCRIPT_USER', DEFAULT_TESTER_SCRIPT_USER)
TESTER_SCRIPT_GROUP = os.environ.get('COGS_TESTER_SCRIPT_GROUP', DEFAULT_TESTER_SCRIPT_GROUP)
