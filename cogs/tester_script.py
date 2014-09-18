# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import copy
import logging
import traceback

import config

import tester


EXTRA_TEST_SCHEMA = ['path_script']
EXTRA_TEST_DEFAULTS = {'path_script': ""}

KEY_SCRIPT = 'script'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Tester(tester.Tester):

    def test(self):

        logger.info(self._format_msg("Running test"))

        # Find Grading Script
        tst_fle = None

        # If user provided path_script, use that
        if self.tst['path_script']:
            script_path = "{:s}/{:s}".format(self.env.wd_tst, self.tst['path_script'])
            script_path = os.path.normpath(script_path)
            for fle in self.env.tst_files:
                fle_path = os.path.normpath(fle['path'])
                if fle_path == script_path:
                    tst_fle = fle
                    break
            if not tst_fle:
                msg = "User specified 'path_script', but file {:s} not found".format(script_path)
                logger.warning(self._format_msg(msg))

        # Next look for any files with the script key
        if not tst_fle:
            count = 0
            for fle in self.env.tst_files:
                key = fle['key']
                if (key == KEY_SCRIPT):
                    tst_fle = fle
                    count += 1
            if (count > 1):
                msg = "Module only supports single test script, but {:d} found".format(count)
                logger.error(self._format_msg(msg))
                raise Exception(msg)

        # Finally, if there is only a single test file, use that
        if not tst_fle:
            if (len(self.env.tst_files) == 1):
                tst_fle = fle

        # Raise error if not found
        if not tst_fle:
            msg = "Module requires a test script file, but none found"
            logger.error(self._format_msg(msg))
            raise Exception(msg)

        # Setup Cmd
        tst_path = tst_fle['path']
        tst_cmd = [tst_path, self.env.wd_sub, self.env.wd_tst]
        os.chmod(tst_path, 0775)
        cmd = tst_cmd

        # Run Script
        score = float(0)
        try:
            ret, stdout, stderr = self.env.run_cmd(cmd)
        except Exception as e:
            msg = "run_cmd raised error: {:s}".format(traceback.format_exc())
            logger.error(self._format_msg(msg))
            ret = 1
            stdout = ""
            stderr = msg

        # Process Results
        if (ret == 0):
            stdout_clean = stdout.rstrip().lstrip()
            try:
                score = float(stdout_clean)
            except Exception as e:
                msg = "Could not convert score '{:s}' to float: {:s}".format(stdout_clean, e)
                logger.error(self._format_msg(msg))
                stderr = msg
                ret = 1
        else:
            msg = "Script returned non-zero value: {:d}".format(ret)
            logger.warning(self._format_msg(msg))
            if not stderr:
                stderr = msg

        # Log Results
        msg = "retval='{:d}', score='{:.2f}', output='{:s}'".format(ret, score, stderr)
        logger.info(self._format_msg(msg))

        # Return
        return ret, score, stderr
