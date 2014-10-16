#!/usr/bin/env python

import sys
import subprocess
import os

SUB_NAMES = ["hello.py", "hello"]

def grade(argv):

    # Extract Paths from Args
    sub_dir = os.path.abspath(argv[0])
    tst_dir = os.path.abspath(argv[1])

    # Check Paths
    if not os.path.exists(sub_dir):
        sys.stderr.write("Could not find submission directory: '{:s}'\n".format(sub_dir))
        return -1
    if not os.path.exists(tst_dir):
        sys.stderr.write("Could not find test directory: '{:s}'\n".format(tst_dir))
        return -1

    # Find submission
    found = False
    for sub_name in SUB_NAMES:
        sub_path = os.path.abspath("{:s}/{:s}".format(sub_dir, sub_name))
        if os.path.exists(sub_path):
            found = True
            break
    if not found:
        sys.stderr.write("Could not find submission: '{:s}'\n".format(SUB_NAMES))
        sys.stderr.write("Does yoru program have a valid name?\n")
        sys.stdout.write("{:2d}\n".format(0))
        return 0

    # Prep Submission
    os.chmod(sub_path, 0775)

    # Grade
    sys.stderr.write("Grading {:s}\n".format(sub_name))
    sys.stderr.write("__________________________\n")

    score = 0
    try:
        p = subprocess.Popen([sub_path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        ret = p.returncode
    except Exception as e:
        sys.stderr.write("Error occured running program: {:s}\n".format(str(e)))
        ret = -1
    else:
        sys.stderr.write("{:s} output:\n {:s}\n".format(sub_name, stdout))

    if (ret == 0):

        # Sanitize Output
        output = stdout.rstrip().lstrip()
        output = output.lower()

        # Grade
        if ("hello" in output):
            sys.stderr.write("Found 'hello' in output -> 5 of 5\n".format(output))
            score += 5
        else:
            sys.stderr.write("Could not find 'hello' in output -> 0 of 5\n".format(output))

        if ("world" in output):
            sys.stderr.write("Found 'world' in output -> 5 of 5\n".format(output))
            score += 5
        else:
            sys.stderr.write("Could not find 'world' in output -> 0 of 5\n".format(output))

    else:

        # Submission Returend Error
        sys.stderr.write("{:s} returned error: {:d} +0\n".format(sub_name, ret))
        sys.stderr.write(str(stderr))

    sys.stderr.write("__________________________\n".format(score))
    sys.stderr.write("Score ---------------> {:2d}\n".format(score))

    sys.stdout.write("{:2d}\n".format(score))

    return 0

if __name__ == "__main__":
    sys.exit(grade(sys.argv[1:]))
