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


EXTRA_TEST_SCHEMA = ['path_solution', 'path_submission', 'prefix_input']
EXTRA_TEST_DEFAULTS = {'path_solution': "", 'path_submission': "", 'prefix_input': ""}

KEY_SOLUTION = 'solution'
KEY_SUBMISSION = 'submission'
KEY_INPUT = 'input'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class Tester(tester.Tester):

    def test(self):

        ## Find Reference Solution
        sol_fle = None

        # If user provided path_solution, use that
        if self.tst['path_solution']:
            sol_path = "{:s}/{:s}".format(self.env.wd_tst, self.tst['path_solution'])
            sol_path = os.path.normpath(sol_path)
            for fle in self.env.tst_files:
                fle_path = os.path.normpath(fle['path'])
                if fle_path == sol_path:
                    sol_fle = fle
                    break
            if not sol_fle:
                msg = "User specified 'path_solution', but file {:s} not found".format(sol_path)
                logger.warning(self._format_msg(msg))

        # Next look for any files with the solution key
        if not sol_fle:
            count = 0
            for fle in self.env.tst_files:
                key = fle['key']
                if (key == KEY_SOLUTION):
                    sol_fle = fle
                    count += 1
            if (count > 1):
                msg = "Module only supports single reference solution, but {:d} found".format(count)
                logger.error(self._format_msg(msg))
                raise Exception(msg)

        # Raise error if not found
        if not sol_fle:
            msg = "Module requires a reference solution, but none found"
            logger.error(self._format_msg(msg))
            raise Exception(msg)

        ## Find Test Submission
        sub_fle = None

        # If user provided path_submission, use that
        if self.tst['path_submission']:
            sub_path = "{:s}/{:s}".format(self.env.wd_tst, self.tst['path_submission'])
            sub_path = os.path.normpath(sub_path)
            for fle in self.env.sub_files:
                fle_path = os.path.normpath(fle['path'])
                if fle_path == sub_path:
                    sub_fle = fle
                    break
            if not sub_fle:
                msg = "User specified 'path_submission', but file {:s} not found".format(sub_path)
                logger.warning(self._format_msg(msg))

        # Next look for any files with the submission key
        if not sub_fle:
            count = 0
            for fle in self.env.sub_files:
                key = fle['key']
                if (key == KEY_SUBMISSION):
                    sub_fle = fle
                    count += 1
            if (count > 1):
                msg = "Module only supports single submission, but {:d} found".format(count)
                logger.error(self._format_msg(msg))
                raise Exception(msg)

        # Raise error if not found
        if not sub_fle:
            msg = "Module requires a submission, but none found"
            logger.error(self._format_msg(msg))
            raise Exception(msg)

        ## Find Input Files
        input_fles = []

        # If user provided prefix_input, use that
        if self.tst['prefix_input']:
            input_prefix = "{:s}/{:s}".format(self.env.wd_tst, self.tst['prefix_input'])
            input_prefix = os.path.normpath(input_prefix)
            for fle in self.env.tst_files:
                fle_path = os.path.normpath(fle['path'])
                if fle_path.startswith(input_prefix):
                    input_fles.append(fle)
                    break
            if not input_fles:
                msg = ("User specified 'prefix_input', " +
                       "but no files starting with {:s} were found".format(input_prefix))
                logger.warning(self._format_msg(msg))

        # Next look for any files with the input key
        if not input_fles:
            for fle in self.env.tst_files:
                key = fle['key']
                if (key == KEY_INPUT):
                    input_fles.append(fle)

        # Add None if no input files found
        if not input_fles:
            input_fles.append(None)

        # Setup Cmd
        sudo_cmd = ['sudo', '-u', config.TESTER_SCRIPT_USER, '-g', config.TESTER_SCRIPT_GROUP]
        sandbox_path = self.env.sandbox['path']
        sandbox_cmd = [sandbox_path]
        os.chmod(sandbox_path, 0775)
        sol_path = sol_fle['path']
        sol_cmd = [sol_path]
        os.chmod(sol_path, 0775)
        sub_path = sub_fle['path']
        sub_cmd = [sub_path]
        os.chmod(sub_path, 0775)

        # Change WD
        owd = os.getcwd()
        msg = "Changing to directory '{:s}'".format(self.env.wd)
        logger.debug(self._format_msg(msg))
        os.chdir(self.env.wd)

        # Run Test Inputs
        ret_val = 0
        pts = 0
        output = ""
        for input_fle in input_fles:

            if input_fle:
                output += "Testing {:s}...\n".format(input_fle['name'])
            else:
                output += "Testing...\n"

            # Test Reference Solution
            if input_fle:
                input_file = open(input_fle['path'], 'r')
            else:
                input_file = None
            cmd = sudo_cmd + sandbox_cmd + sol_cmd
            msg = "Preparing to run '{:s}'".format(cmd)
            logger.info(self._format_msg(msg))
            ret = 1
            stdout = ""
            stderr = ""
            try:
                p = subprocess.Popen(cmd, env=self.env.env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=input_file)
                stdout, stderr = p.communicate()
                ret = p.returncode
            except Exception as e:
                output += "Exception running reference solution: {:s}\n".format(str(e))
            finally:
                if input_file:
                    input_file.close()

            # Process Solution Output
            if stderr:
                output += "Error output running reference solution: {:s}\n".format(stderr)
            if (ret != 0):
                output += "Non-zero exit running reference solution: {:d}\n".format(ret)
                ret_val += ret
                continue
            exp = stdout.rstrip().lstrip()

            # Test Submission
            if input_fle:
                input_file = open(input_fle['path'], 'r')
            else:
                input_file = None
            cmd = sudo_cmd + sandbox_cmd + sub_cmd
            msg = "Preparing to run '{:s}'".format(cmd)
            logger.info(self._format_msg(msg))
            ret = 1
            stdout = ""
            stderr = ""
            try:
                p = subprocess.Popen(cmd, env=self.env.env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=input_file)
                stdout, stderr = p.communicate()
                ret = p.returncode
            except Exception as e:
                output += "Exception running submission: {:s}\n".format(str(e))
            finally:
                if input_file:
                    input_file.close()

            # Process Solution Output
            if stderr:
                output += "Error output running submission: {:s}\n".format(stderr)
            if (ret != 0):
                output += "Non-zero exit running submission: {:d}\n".format(ret)
            rec = stdout.rstrip().lstrip()

            output += "Expected: '{:s}', Received: '{:s}'".format(exp, rec)
            if (rec == exp):
                output += "   +1 pts\n"
                pts += 1
            else:
                output += "   +0 pts\n"

        # Change Back to OWD
        msg = "Changing back to directory '{:s}'".format(owd)
        logger.debug(self._format_msg(msg))
        os.chdir(owd)

        # Calculate Score
        score = (pts / float(len(input_fles))) * float(self.tst['maxscore'])

        # Log Results
        msg = "retval='{:d}', score='{:.2f}', output='{:s}'".format(ret_val, score, output)
        logger.info(self._format_msg(msg))

        # Return
        return ret_val, score, output
