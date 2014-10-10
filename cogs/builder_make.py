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

        # Setup Cmd
        tst_path = tst_fle['path']
        tst_cmd = [tst_path, self.env.wd_sub, self.env.wd_tst]
        os.chmod(tst_path, 0775)
        cmd = tst_cmd

        # Call Make
        cmd = ['make']
        try:
            ret, out = self.env.run_cmd(cmd, combine=True)
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
