# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os

# Set Paths
MOD_PATH = os.path.dirname(os.path.realpath(__file__))
ROOT_PATH = os.path.realpath("{:s}/..".format(MOD_PATH))

# Set Default Vals
DEFAULT_GRADER_MOODLE_USERNAME = None
DEFAULT_GRADER_MOODLE_PASSWORD = None
DEFAULT_SCRIPT_PATH = os.path.realpath("{:s}/scripts".format(ROOT_PATH))

# Get Env Vars
GRADER_MOODLE_USERNAME = os.environ.get('COGS_GRADER_MOODLE_USERNAME', DEFAULT_GRADER_MOODLE_USERNAME)
GRADER_MOODLE_PASSWORD = os.environ.get('COGS_GRADER_MOODLE_PASSWORD', DEFAULT_GRADER_MOODLE_PASSWORD)
SCRIPT_PATH = os.environ.get('COGS_SCRIPT_PATH', DEFAULT_SCRIPT_PATH)
