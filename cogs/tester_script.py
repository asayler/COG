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


KEY_SCRIPT = 'script'


class Tester(object):

    def __init__(self, env, data):
        self.env = env
        self.data = data

    def test(self):

        # Find Grading Script
        tst_fle = None
        count = 0
        for fle in self.env.tst_files:
            key = fle['key']
            if (key == KEY_SCRIPT):
                tst_fle = fle
                count += 1
        if not tst_fle:
            raise Exception("Tester module requires a test script file")
        if (count > 1):
            raise Exception("Tester module only supports suppling one test script file")

        # Setup Cmd
        sudo_cmd = ['sudo', '-u', config.TESTER_SCRIPT_USER, '-g', config.TESTER_SCRIPT_GROUP]
        sandbox_path = self.env.sandbox['path']
        sandbox_cmd = [sandbox_path]
        os.chmod(sandbox_path, 0775)
        tst_path = tst_fle['path']
        tst_cmd = [tst_path, self.env.wd_sub]
        os.chmod(tst_path, 0775)
        cmd = sudo_cmd + sandbox_cmd + tst_cmd

        # Change WD
        owd = os.getcwd()
        try:
            os.chdir(self.env.wd)
        except:
            raise

        # Run Script
        score = float('nan')
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env.env)
            stdout, stderr = p.communicate()
            ret = p.returncode
        except Exception as e:
            stdout = "0"
            stderr = str(e)
            retcode = -1

        # Change Back to OWD
        try:
            os.chdir(owd)
        except:
            raise

        # Process Results
        if (ret == 0):
            stdout_clean = stdout.rstrip().lstrip()
            try:
                score = float(stdout_clean)
            except Exception as e:
                score = str(e)
        else:
            score = 0

        # Return
        return ret, score, stderr
