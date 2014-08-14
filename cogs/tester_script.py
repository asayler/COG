# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import stat
import subprocess
import mimetypes

TOTAL_TIME_LIMIT = 30 #seconds
CPU_TIME_LIMIT = 10 #seconds
PROC_LIMIT = 1000 #processes
FILE_SIZE = 100 #blocks
MEM_LIMIT = 10240 #kB
TEST_USER = "nobody"
TEST_GROUP = "nogroup"

class Tester(object):

    def __init__(self, env):
        self.env = env

    def test(self):

        if (len(self.env.tst_files) != 1):
            raise Exception("Script only supports a single test script file")

        score = float('nan')
        tst_pgm = self.env.tst_files[0]['path']

        # Make Executable
        os.chmod(tst_pgm, 0777)

        # Change WD
        owd = os.getcwd()
        try:
            os.chdir(self.env.wd)
        except:
            raise

        # Run Script
        ulimit = "ulimit -t {:d} -u {:d}".format(CPU_TIME_LIMIT, PROC_LIMIT)
        # ulimit = "ulimit -t {:d} -u {:d} -f {:d} -m {:d}".format(CPU_TIME_LIMIT,
        #                                                          PROC_LIMIT,
        #                                                          FILE_SIZE,
        #                                                          MEM_LIMIT)
        timeout = "timeout {:d}".format(TOTAL_TIME_LIMIT)
        sudo = "sudo -u {:s} -g {:s}".format(TEST_USER, TEST_GROUP)

        cmd = "{:s} && {:s}".format(ulimit, tst_pgm)

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 shell=True, executable="/bin/bash")
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
                score = 0

        # Return
        return ret, score, stderr
