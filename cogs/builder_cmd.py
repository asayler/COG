# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import copy
import logging
import traceback

import config

import builder


EXTRA_TEST_SCHEMA = ['builder_cmd']
EXTRA_TEST_DEFAULTS = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Builder(builder.Builder):

    def build(self):

        # Set Vars
        ret = -1
        score = "0"
        stderr = "Dummy Builder Build()"

        # Return
        return ret_val, output
