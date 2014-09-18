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

        # Call Parent
        super(Tester, self).test()
        msg = "testmod_io: Running test"
        logger.info(self._format_msg(msg))

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
                msg = "testmod_io: User specified 'path_solution', "
                msg += "but file {:s} not found".format(sol_path)
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
                msg = "testmod_io: Module only supports single reference solution, "
                msg += "but {:d} found".format(count)
                logger.error(self._format_msg(msg))
                raise Exception(msg)

        # Raise error if not found
        if not sol_fle:
            msg = "testmod_io: Module requires a reference solution, but none found"
            logger.error(self._format_msg(msg))
            raise Exception(msg)

        ## Find Test Submission
        sub_fle = None

        # If user provided path_submission, use that
        if self.tst['path_submission']:
            sub_path = "{:s}/{:s}".format(self.env.wd_sub, self.tst['path_submission'])
            sub_path = os.path.normpath(sub_path)
            for fle in self.env.sub_files:
                fle_path = os.path.normpath(fle['path'])
                if fle_path == sub_path:
                    sub_fle = fle
                    break
            if not sub_fle:
                msg = "testmod_io: User specified 'path_submission', "
                msg += "but file {:s} not found".format(sub_path)
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
                msg = "testmod_io: Module only supports single submission, "
                msg += "but {:d} found".format(count)
                logger.error(self._format_msg(msg))
                raise Exception(msg)

        # Finally, if there is only a single submission file, use that
        if not sub_fle:
            if (len(self.env.sub_files) == 1):
                sub_fle = fle

        # Raise error if not found
        if not sub_fle:
            msg = "testmod_io: Module requires a submission, but none found"
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
            if not input_fles:
                msg = "testmod_io: User specified 'prefix_input', "
                msg += "but no files starting with {:s} were found".format(input_prefix))
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
        sol_path = sol_fle['path']
        sol_cmd = [sol_path]
        os.chmod(sol_path, 0775)
        sub_path = sub_fle['path']
        sub_cmd = [sub_path]
        os.chmod(sub_path, 0775)

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
            cmd = sol_cmd
            ret = 1
            stdout = ""
            stderr = ""
            try:
                ret, stdout, stderr = self.env.run_cmd(cmd, stdin=input_file)
            except Exception as e:
                output += "run_cmd raised error: {:s}\n".format(traceback.format_exc())
                continue
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
            cmd = sub_cmd
            ret = 1
            stdout = ""
            stderr = ""
            try:
                ret, stdout, stderr = self.env.run_cmd(cmd, stdin=input_file)
            except Exception as e:
                output += "run_cmd raised error: {:s}\n".format(traceback.format_exc())
                continue
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
                output += "   CORRECT\n"
                pts += 1
            else:
                output += "   WRONG\n"

        # Calculate Score
        score = (pts / float(len(input_fles))) * float(self.tst['maxscore'])

        # Log Results
        msg = "testmod_io: retval='{:d}', score='{:.2f}'".format(ret_val, score)
        logger.info(self._format_msg(msg))

        # Return
        return ret_val, score, output
