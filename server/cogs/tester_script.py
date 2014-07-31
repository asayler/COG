# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import stat
import subprocess
import mimetypes

class Tester(object):

    def __init__(self, env):
        self.env = env

    def test(self):

        if (len(self.env.tst_files) != 1):
            raise Exception("Script only supports a single test script file")

        score = float('nan')
        tst_pgm = self.env.tst_files[0]['path']

        # Make Executable
        os.chmod(tst_pgm, 0775)

        # Change WD
        owd = os.getcwd()
        try:
            os.chdir(self.env.wd)
        except:
            raise

        # Run Script
        try:
            p = subprocess.Popen([tst_pgm], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            ret = p.returncode
        except:
            raise

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
            except:
                raise

        # Return
        return ret, score, stderr
