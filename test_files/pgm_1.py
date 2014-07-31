#!/usr/bin/env python

import sys

if len(sys.argv) != 3:
    sys.stderr.write("Usage: {:s} <num> <num>\n".format(sys.argv[0]))
    exit(1)

s = float(sys.argv[1]) + float(sys.argv[2])

print("{:.2f}".format(s))
exit(0)
