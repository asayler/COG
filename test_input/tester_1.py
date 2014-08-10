#!/usr/bin/env python

import sys
import random
import subprocess

PGM = "python"
SUB = "./pgm.py"

sys.stderr.write("Grading {:s}...\n".format(SUB))

score = 0

random.seed()
for i in range(10):
    x = random.randint(0, 33)
    y = random.randint(0, 33)
    e = x + y

    sys.stderr.write("Trying ({:2d} + {:2d})...\n".format(x, y))
    try:
        p = subprocess.Popen([PGM, SUB, str(x), str(y)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        ret = p.returncode
    except:
        raise

    if (ret == 0):
        stdout_clean = stdout.rstrip().lstrip()
        try:
            s = int(float(stdout_clean))
        except:
            raise

        if (s == e):
            sys.stderr.write("Got {:2d}, Expecting {:2d}... +1\n".format(s, e))
            score += 1
        else:
            sys.stderr.write("Got {:2d}, Expecting {:2d}... +0\n".format(s, e))
            score += 0

    else:
        sys.stderr.write("{:s} returned error: {:d}... +0\n".format(SUB, ret))
        sys.stderr.write(str(stderr))

sys.stderr.write("{:s} Graded... Score = {:2d}\n".format(SUB, score))
sys.stdout.write("{:d}\n".format(score))
