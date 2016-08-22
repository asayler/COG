# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# University of Colorado

import ConfigParser
import os

config = ConfigParser.SafeConfigParser(allow_no_value=True)

# Sections
SEC_CORE = "core"
config.add_section(SEC_CORE)
SEC_REDIS = "redis"
config.add_section(SEC_REDIS)
SEC_FILESTORAGE = "filestorage"
config.add_section(SEC_FILESTORAGE)
SEC_PERMS = "permissions"
config.add_section(SEC_PERMS)
SEC_LOGGING = "logging"
config.add_section(SEC_LOGGING)
SEC_REPMOD_MOODLE = "repmod_moodle"
config.add_section(SEC_REPMOD_MOODLE)
SEC_AUTHMOD_MOODLE = "authmod_moodle"
config.add_section(SEC_AUTHMOD_MOODLE)
SEC_AUTHMOD_LDAP = "authmod_ldap"
config.add_section(SEC_AUTHMOD_LDAP)
SEC_ENV_LOCAL = "env_local"
config.add_section(SEC_ENV_LOCAL)

# Set Paths
MOD_PATH = os.path.dirname(os.path.realpath(__file__))
ROOT_PATH = os.path.realpath("{:s}/..".format(MOD_PATH))
SCRIPTS_PATH = os.path.realpath("{:s}/{:s}".format(ROOT_PATH, "scripts"))
CONF_PATH = os.path.realpath("{:s}/{:s}".format(ROOT_PATH, "cog.conf"))

# Set Default Vals
config.set(SEC_CORE, 'MAX_OUTPUT', "1000000")
config.set(SEC_REDIS, 'HOST', "localhost")
config.set(SEC_REDIS, 'PORT', "6379")
config.set(SEC_REDIS, 'DB', "4")
config.set(SEC_REDIS, 'PASSWORD', None)
config.set(SEC_FILESTORAGE, 'PATH', "{:s}/files".format(ROOT_PATH))
config.set(SEC_PERMS, 'PATH', "{:s}/perms".format(ROOT_PATH))
config.set(SEC_LOGGING, 'ENABLED', "True")
config.set(SEC_LOGGING, 'PATH', "{:s}/logs".format(ROOT_PATH))
config.set(SEC_AUTHMOD_MOODLE, 'HOST', None)
config.set(SEC_AUTHMOD_MOODLE, 'SERVICE', None)
config.set(SEC_AUTHMOD_LDAP, 'HOST', None)
config.set(SEC_AUTHMOD_LDAP, 'BASEDN', None)
config.set(SEC_REPMOD_MOODLE, 'HOST', None)
config.set(SEC_REPMOD_MOODLE, 'SERVICE', None)
config.set(SEC_REPMOD_MOODLE, 'USERNAME', None)
config.set(SEC_REPMOD_MOODLE, 'PASSWORD', None)
config.set(SEC_ENV_LOCAL, 'SANDBOX_SCRIPT', "local_sandbox.py")
config.set(SEC_ENV_LOCAL, 'USER', "nobody")
config.set(SEC_ENV_LOCAL, 'GROUP', "nogroup")
config.set(SEC_ENV_LOCAL, 'LIMIT_TIME_CPU', "1")
config.set(SEC_ENV_LOCAL, 'LIMIT_TIME_WALL', "10")

DEFAULT_ENV_LOCAL_TMP_PATH = "/tmp/cogs/envs"
DEFAULT_ARCHIVE_PATH = "/tmp/cogs/archives"
DEFAULT_UPLOAD_PATH = "/tmp/cogs/uploads"

# Read Config File
config.read(CONF_PATH)

# Get Env Var Overrides
CORE_MAX_OUTPUT = int(os.environ.get('COGS_CORE_MAX_OUTPUT', config.get(SEC_CORE, 'MAX_OUTPUT')))
REDIS_HOST = os.environ.get('COGS_REDIS_HOST', config.get(SEC_REDIS, 'HOST'))
REDIS_PORT = int(os.environ.get('COGS_REDIS_PORT', config.get(SEC_REDIS, 'PORT')))
REDIS_DB = int(os.environ.get('COGS_REDIS_DB', config.get(SEC_REDIS, 'DB')))
REDIS_PASSWORD = os.environ.get('COGS_REDIS_PASSWORD', config.get(SEC_REDIS, 'PASSWORD'))
FILESTORAGE_PATH = os.environ.get('COGS_FILESTORAGE_PATH', config.get(SEC_FILESTORAGE, 'PATH'))
FILESTORAGE_PATH = os.path.realpath(FILESTORAGE_PATH)
PERMS_PATH = os.environ.get('COGS_PERMS_PATH', config.get(SEC_PERMS, 'PATH'))
PERMS_PATH = os.path.realpath(PERMS_PATH)
ARCHIVE_PATH = os.path.realpath(DEFAULT_ARCHIVE_PATH)
UPLOAD_PATH = os.path.realpath(DEFAULT_UPLOAD_PATH)
LOGGING_ENABLED = os.environ.get('COGS_LOGGING_ENABLED', config.get(SEC_LOGGING, 'ENABLED'))
LOGGING_ENABLED = LOGGING_ENABLED.lower() in ['true', 'yes', 'on', '1']
LOGGING_PATH = os.environ.get('COGS_LOGGING_PATH', config.get(SEC_LOGGING, 'PATH'))
LOGGING_PATH = os.path.realpath(LOGGING_PATH)
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
AUTHMOD_LDAP_HOST = os.environ.get('COGS_AUTHMOD_LDAP_HOST',
                                    config.get(SEC_AUTHMOD_LDAP, 'HOST'))
AUTHMOD_LDAP_BASEDN = os.environ.get('COGS_AUTHMOD_LDAP_BASEDN',
                                    config.get(SEC_AUTHMOD_LDAP, 'BASEDN'))
ENV_LOCAL_LIMIT_TIME_CPU = float(os.environ.get('COGS_ENV_LOCAL_LIMIT_TIME_CPU',
                                    config.get(SEC_ENV_LOCAL, 'LIMIT_TIME_CPU')))
ENV_LOCAL_LIMIT_TIME_WALL = float(os.environ.get('COGS_ENV_LOCAL_LIMIT_TIME_WALL',
                                    config.get(SEC_ENV_LOCAL, 'LIMIT_TIME_WALL')))

ENV_LOCAL_SANDBOX_SCRIPT = config.get(SEC_ENV_LOCAL, 'SANDBOX_SCRIPT')
ENV_LOCAL_USER = config.get(SEC_ENV_LOCAL, 'USER')
ENV_LOCAL_GROUP = config.get(SEC_ENV_LOCAL, 'GROUP')

ARCHIVE_PATH = os.environ.get('COGS_ARCHIVE_PATH', DEFAULT_ARCHIVE_PATH)
UPLOAD_PATH = os.environ.get('COGS_UPLOAD_PATH', DEFAULT_UPLOAD_PATH)
ENV_LOCAL_TMP_PATH = os.environ.get('COGS_ENV_LOCAL_TMP_PATH', DEFAULT_ENV_LOCAL_TMP_PATH)
