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

EXTRA_TEST_SCHEMA = []
EXTRA_TEST_DEFAULTS = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Builder(builder.Builder):

    def build(self):

        # Call Parent
        msg = "Running build"
        logger.info(self._format_msg(msg))

        # Call Make
        cmd = ['make']
        try:
            ret, out, err = self.env.run_cmd(cmd, combine=True, cwd=self.env.wd_sub)
        except Exception as e:
            msg = "run_cmd raised error: {:s}".format(traceback.format_exc())
            logger.error(self._format_msg(msg))
            ret = 1
            out = msg
        else:
            # Process Results
            if ret:
                msg = "make returned non-zero value: {:d}".format(ret)
                logger.warning(self._format_msg(msg))

        # Log Results
        msg = "ret='{:d}'".format(ret)
        logger.info(self._format_msg(msg))

        # Return
        return ret, out
