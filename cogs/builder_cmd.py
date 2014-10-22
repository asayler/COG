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


EXTRA_TEST_SCHEMA = ['builder_cmd', 'builder_cmd_sep']
EXTRA_TEST_DEFAULTS = {'builder_cmd_sep': ""}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Builder(builder.Builder):

    def build(self):

        # Call Parent
        msg = "Running build"
        logger.info(self._format_msg(msg))

        # Get Cmd
        sep = self.tst['builder_cmd_sep']
        if not sep:
            sep = None
        cmd = self.tst['builder_cmd']
        cmd = cmd.split(sep)
        cmd = filter(lambda x: len(x), cmd)
        if not len(cmd):
            msg = "build cmd must not be null"
            logger.error(self._format_msg(msg))
            raise Exception(msg)

        # Call Cmd
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
                msg = "build cmd returned non-zero value: {:d}".format(ret)
                logger.warning(self._format_msg(msg))

        # Log Results
        msg = "ret='{:d}'".format(ret)
        logger.info(self._format_msg(msg))

        # Return
        return ret, out
