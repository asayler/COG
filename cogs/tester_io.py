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

import config

KEY_SOLUTION = 'solution'
KEY_SUBMISSION = 'submission'
KEY_INPUT = 'input'

class Tester(object):

    def __init__(self, env):
        self.env = env

    def test(self):

        # Find Reference Submission
        sol_fle = None
        count = 0
        for fle in self.env.tst_files:
            key = fle['key']
            if (key == KEY_SOLUTION):
                sol_fle = fle
                count += 1
        if not sol_fle:
            raise Exception("Tester module requires a reference solution file")
        if (count > 1):
            raise Exception("Tester module only supports suppling one solution file")

        # Find Test Submission
        sub_fle = None
        count = 0
        for fle in self.env.sub_files:
            key = fle['key']
            if (key == KEY_SUBMISSION):
                sub_fle = fle
                count += 1
        if not sub_fle:
            raise Exception("Tester module requires a submission file")
        if (count > 1):
            raise Exception("Tester module only supports suppling one submission file")

        # Find Input Files
        input_fles = []
        for fle in self.env.tst_files:
            key = fle['key']
            if (key == KEY_INPUT):
                input_fles.append(fle)
        if not input_fles:
            raise Exception("Tester module requires at least one input file")

        # Setup Cmd
        sudo_cmd = ['sudo', '-u', config.TESTER_SCRIPT_USER, '-g', config.TESTER_SCRIPT_GROUP]
        sandbox_path = self.env.sandbox['path']
        sandbox_cmd = [sandbox_path]
        os.chmod(sandbox_path, 0775)
        sol_path = sol_fle['path']
        sol_cmd = [sol_path]
        os.chmod(tst_path, 0775)
        sol_path = sol_fle['path']
        sol_cmd = [sol_path]
        os.chmod(tst_path, 0775)

        # Change WD
        owd = os.getcwd()
        try:
            os.chdir(self.env.wd)
        except:
            raise

        ret_val = 0
        score = 0
        output = ""
        for input_fle in input_fles:

            output += "Testing {:s}...\n".format(input_fle['name'])

            # Test Reference Solution
            input_file = open(input_fle['path'], 'r')
            cmd = sudo_cmd + sandbox_cmd + sol_cmd
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
            input_file = open(input_fle['path'], 'r')
            cmd = sudo_cmd + sandbox_cmd + sub_cmd
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
                input_file.close()

            # Process Solution Output
            if stderr:
                output += "Error output running submission: {:s}\n".format(stderr)
            if (ret != 0):
                output += "Non-zero exit running submission: {:d}\n".format(ret)
            rec = stdout.rstrip().lstrip()

            output += "Expected: {:s}, Received: {:s}".format(exp, rec)
            if (rec == exp):
                output += "   +1 pts\n"
                score += 1
            else:
                output += "   +0 pts\n"

        # Change Back to OWD
        try:
            os.chdir(owd)
        except:
            raise

        # Return
        return ret_val, score, output
