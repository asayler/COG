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
        os.chmod(tst_pgm, 775)

        try:
            p = subprocess.Popen([tst_pgm], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
        except:
            raise

        if (p.returncode == 0):
            stdout_clean = stdout.rstrip().lstrip()
            try:
                score = float(stdout_clean)
            except:
                raise

        return p.returncode, score, stderr
