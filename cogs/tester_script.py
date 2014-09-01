# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import stat
import subprocess
import mimetypes
import shutil
import copy
import logging

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

        # Find Grading Script
        tst_fle = None

        # If user provided path_script, use that
        if self.tst['path_script']:
            script_path = "{:s}\{:s}".format(self.env.wd_test, self.tst['path_script'])
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

        # Raise error if not found
        if not tst_fle:
            msg = "Module requires a test script file, but none found"
            logger.error(self._format_msg(msg))
            raise Exception(msg)

        # Setup Cmd
        sudo_cmd = ['sudo', '-u', config.TESTER_SCRIPT_USER, '-g', config.TESTER_SCRIPT_GROUP]
        sandbox_path = self.env.sandbox['path']
        sandbox_cmd = [sandbox_path]
        os.chmod(sandbox_path, 0775)
        tst_path = tst_fle['path']
        tst_cmd = [tst_path, self.env.wd_sub]
        os.chmod(tst_path, 0775)
        cmd = sudo_cmd + sandbox_cmd + tst_cmd
        msg = "Preparing to run '{:s}'".format(cmd)
        logger.info(self._format_msg(msg))

        # Change WD
        owd = os.getcwd()
        msg = "Changing to directory '{:s}'".format(self.env.wd)
        logger.debug(self._format_msg(msg))
        os.chdir(self.env.wd)

        # Run Script
        score = float('nan')
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env.env)
            stdout, stderr = p.communicate()
            ret = p.returncode
        except Exception as e:
            msg = "Script raised error: {:s}".format(e)
            logger.error(self._format_msg(msg))
            stderr = msg
            retcode = -1

        # Change Back to OWD
        msg = "Changing back to directory '{:s}'".format(owd)
        logger.debug(self._format_msg(msg))
        os.chdir(owd)

        # Process Results
        if (ret == 0):
            stdout_clean = stdout.rstrip().lstrip()
            try:
                score = float(stdout_clean)
            except Exception as e:
                msg = "Could not convert score '{:s}' to float: {:s}".format(score, e)
                logger.error(self._format_msg(msg))
                stderr = msg
        else:
            score = 0

        # Log Results
        msg = "ret='{:d}', score='{:.2f}', stderr='{:s}'".format(ret, score, stderr)
        logger.info(self._format_msg(msg))

        # Return
        return ret, score, stderr
