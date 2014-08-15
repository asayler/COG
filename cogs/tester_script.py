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

    def __init__(self, env):
        self.env = env

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

        # Change WD
        owd = os.getcwd()
        try:
            os.chdir(self.env.wd)
        except:
            raise

        # Copy Sandbox
        sandbox_exe = config.TESTER_SCRIPT_SANDBOX
        sandbox_src = os.path.realpath("{:s}/{:s}".format(config.SCRIPT_PATH, sandbox_exe))
        sandbox_dst = os.path.realpath("{:s}/{:s}".format(self.env.wd, sandbox_exe))
        shutil.copy(sandbox_src, sandbox_dst)

        # Setup Cmd
        tst_path = tst_fle['path']
        tst_cmd = [tst_path]
        os.chmod(tst_path, 0775)
        sandbox_path = sandbox_dst
        sandbox_cmd = [sandbox_path]
        os.chmod(sandbox_path, 0775)
        sudo_cmd = ['sudo', '-u', config.TESTER_SCRIPT_USER, '-g', config.TESTER_SCRIPT_GROUP]
        cmd = sudo_cmd + sandbox_cmd + tst_cmd

        # Clean ENV
        env = {}
        for var in os.environ:
            if not var.startswith("COGS"):
                env[var] = os.environ[var]

        # Run Script
        score = float('nan')
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            stdout, stderr = p.communicate()
            ret = p.returncode
        except Exception as e:
            ret = str(e)

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
            score = ""

        # Return
        return ret, score, stderr
