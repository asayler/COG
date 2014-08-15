#!/usr/bin/env python


import sys
import random
import subprocess
import time
import os

PGM = "python"
SUB_NAME = "add.py"


def grade(argv):

    sub_path = os.path.abspath("{:s}/{:s}".format(argv[0], SUB_NAME))

    sys.stderr.write("Grading {:s}\n".format(sub_path))
    sys.stderr.write("__________________________\n")

    score = 0

    random.seed()
    for i in range(10):

        x = random.randint(0, 33)
        y = random.randint(0, 33)
        e = x + y

        sys.stderr.write("Trying ({:2d} + {:2d})...\n".format(x, y))
        try:
            p = subprocess.Popen([PGM, sub_path], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate("{:d}\n{:d}".format(x, y))
            ret = p.returncode
        except Exception as e:
            sys.stderr.write("Error occured running program: {:s}\n".format(str(e)))
            ret = None

        if (ret == 0):

            stdout = stdout.split()[-1].rstrip().lstrip()
            try:
                s = int(float(stdout))
            except Exception as e:
                sys.stderr.write("Failed to convert '{:s}' to number: {:s}\n".format(stdout, str(e)))
                s = None

            if s is not None:
                if (s == e):
                    sys.stderr.write("Got {:2d}, Expecting {:2d}   +1\n".format(s, e))
                    score += 1
                else:
                    sys.stderr.write("Got {:2d}, Expecting {:2d}   +0\n".format(s, e))
                    score += 0

        else:
            sys.stderr.write("{:s} returned error: {:d} +0\n".format(sub_path, ret))
            sys.stderr.write(str(stderr))

        w = random.randint(0, 10)
        time.sleep(w/100.0)

    sys.stderr.write("__________________________\n".format(score))
    sys.stderr.write("Score ---------------> {:2d}\n".format(score))

    sys.stdout.write("{:2d}\n".format(score))

    return 0

if __name__ == "__main__":
    sys.exit(grade(sys.argv[1:]))
